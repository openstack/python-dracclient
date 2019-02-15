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
import subprocess
import time

from dracclient import constants
from dracclient import exceptions
from dracclient.resources import bios
from dracclient.resources import idrac_card
from dracclient.resources import inventory
from dracclient.resources import job
from dracclient.resources import lifecycle_controller
from dracclient.resources import nic
from dracclient.resources import raid
from dracclient.resources import system
from dracclient.resources import uris
from dracclient import utils
from dracclient import wsman

IDRAC_IS_READY = "LC061"

LOG = logging.getLogger(__name__)


class DRACClient(object):
    """Client for managing DRAC nodes"""

    BIOS_DEVICE_FQDD = 'BIOS.Setup.1-1'
    IDRAC_FQDD = 'iDRAC.Embedded.1'

    def __init__(
            self, host, username, password, port=443, path='/wsman',
            protocol='https',
            ssl_retries=constants.DEFAULT_WSMAN_SSL_ERROR_RETRIES,
            ssl_retry_delay=constants.DEFAULT_WSMAN_SSL_ERROR_RETRY_DELAY_SEC,
            ready_retries=constants.DEFAULT_IDRAC_IS_READY_RETRIES,
            ready_retry_delay=(
                constants.DEFAULT_IDRAC_IS_READY_RETRY_DELAY_SEC)):
        """Creates client object

        :param host: hostname or IP of the DRAC interface
        :param username: username for accessing the DRAC interface
        :param password: password for accessing the DRAC interface
        :param port: port for accessing the DRAC interface
        :param path: path for accessing the DRAC interface
        :param protocol: protocol for accessing the DRAC interface
        :param ssl_retries: number of resends to attempt on SSL failures
        :param ssl_retry_delay: number of seconds to wait between
                                retries on SSL failures
        :param ready_retries: number of times to check if the iDRAC is
                              ready
        :param ready_retry_delay: number of seconds to wait between
                                  checks if the iDRAC is ready
        """
        self.client = WSManClient(host, username, password, port, path,
                                  protocol, ssl_retries, ssl_retry_delay,
                                  ready_retries, ready_retry_delay)
        self._job_mgmt = job.JobManagement(self.client)
        self._power_mgmt = bios.PowerManagement(self.client)
        self._boot_mgmt = bios.BootManagement(self.client)
        self._bios_cfg = bios.BIOSConfiguration(self.client)
        self._lifecycle_cfg = lifecycle_controller.LCConfiguration(self.client)
        self._idrac_cfg = idrac_card.iDRACCardConfiguration(self.client)
        self._raid_mgmt = raid.RAIDManagement(self.client)
        self._system_cfg = system.SystemConfiguration(self.client)
        self._inventory_mgmt = inventory.InventoryManagement(self.client)
        self._nic_cfg = nic.NICConfiguration(self.client)

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
        :returns: a dictionary containing:
                 - The is_commit_required key with a boolean value indicating
                   whether a config job must be created for the values to be
                   applied.
                 - The is_reboot_required key with a RebootRequired enumerated
                   value indicating whether the server must be rebooted for the
                   values to be applied.  Possible values are true and false.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        :raises: InvalidParameterValue on invalid BIOS attribute
        """
        return self._bios_cfg.set_bios_settings(settings)

    def list_idrac_settings(self, by_name=False, fqdd_filter=IDRAC_FQDD):
        """List the iDRAC configuration settings

        :param by_name: Controls whether returned dictionary uses iDRAC card
                        attribute name as key. If set to False, instance_id
                        will be used.  If set to True the keys will be of the
                        form "group_id#name".
        :param fqdd_filter: An FQDD used to filter the instances.  Note that
                            this is only used when by_name is True.
        :returns: a dictionary with the iDRAC settings using instance_id as the
                  key except when by_name is True. The attributes are either
                  iDRACCardEnumerableAttribute, iDRACCardStringAttribute or
                  iDRACCardIntegerAttribute objects.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._idrac_cfg.list_idrac_settings(by_name=by_name,
                                                   fqdd_filter=fqdd_filter)

    def set_idrac_settings(self, settings, idrac_fqdd=IDRAC_FQDD):
        """Sets the iDRAC configuration settings

        To be more precise, it sets the pending_value parameter for each of the
        attributes passed in. For the values to be applied, a config job may
        need to be created and the node may need to be rebooted.

        :param settings: a dictionary containing the proposed values, with
                         each key being the name of attribute qualified with
                         the group ID in the form "group_id#name" and the value
                         being the proposed value.
        :param idrac_fqdd: the FQDD of the iDRAC.
        :returns: a dictionary containing:
                 - The is_commit_required key with a boolean value indicating
                   whether a config job must be created for the values to be
                   applied.
                 - The is_reboot_required key with a RebootRequired enumerated
                   value indicating whether the server must be rebooted for the
                   values to be applied.  Possible values are true and false.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        :raises: InvalidParameterValue on invalid attribute
        """
        return self._idrac_cfg.set_idrac_settings(settings, idrac_fqdd)

    def reset_idrac(self, force=False, wait=False,
                    ready_wait_time=30):
        """Resets the iDRAC and optionally block until reset is complete.

        :param force: does a force reset when True and a graceful reset when
               False
        :param wait: returns immediately after reset if False, or waits
                for the iDRAC to return to operational state if True
        :param ready_wait_time: the amount of time in seconds to wait after
                the reset before starting to check on the iDRAC's status
        :returns: True on success, raises exception on failure
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on failure to reset iDRAC
        """
        return_value = self._idrac_cfg.reset_idrac(force)
        if not wait and return_value:
            return return_value

        if not return_value:
            raise exceptions.DRACOperationFailed(
                drac_messages="Failed to reset iDRAC")

        LOG.debug("iDRAC was reset, waiting for return to operational state")

        state_reached = self._wait_for_host_state(
            self.client.host,
            alive=False,
            ping_count=2,
            retries=24)

        if not state_reached:
            raise exceptions.DRACOperationFailed(
                drac_messages="Timed out waiting for the %s iDRAC to become "
                "not pingable" % self.client.host)

        LOG.info("The iDRAC has become not pingable")

        state_reached = self._wait_for_host_state(
            self.client.host,
            alive=True,
            ping_count=3,
            retries=24)

        if not state_reached:
            raise exceptions.DRACOperationFailed(
                drac_messages="Timed out waiting for the %s iDRAC to become "
                "pingable" % self.client.host)

        LOG.info("The iDRAC has become pingable")
        LOG.info("Waiting for the iDRAC to become ready")
        time.sleep(ready_wait_time)

        self.client.wait_until_idrac_is_ready()

    def _ping_host(self, host):
        response = subprocess.call(
            "ping -c 1 {} 2>&1 1>/dev/null".format(host), shell=True)
        return (response == 0)

    def _wait_for_host_state(self,
                             host,
                             alive=True,
                             ping_count=3,
                             retries=24):
        if alive:
            ping_type = "pingable"

        else:
            ping_type = "not pingable"

        LOG.info("Waiting for the iDRAC to become %s", ping_type)

        response_count = 0
        state_reached = False

        while retries > 0 and not state_reached:
            response = self._ping_host(host)
            retries -= 1
            if response == alive:
                response_count += 1
                LOG.debug("The iDRAC is %s, count=%s",
                          ping_type,
                          response_count)
                if response_count == ping_count:
                    LOG.debug("Reached specified ping count")
                    state_reached = True
            else:
                response_count = 0
                if alive:
                    LOG.debug("The iDRAC is still not pingable")
                else:
                    LOG.debug("The iDRAC is still pingable")
            time.sleep(10)

        return state_reached

    def commit_pending_idrac_changes(
            self,
            idrac_fqdd=IDRAC_FQDD,
            reboot=False,
            start_time='TIME_NOW'):
        """Create a config job for applying all pending iDRAC changes.

        :param idrac_fqdd: the FQDD of the iDRAC.
        :param reboot: indication of whether to also create a reboot job
        :param start_time: start time for job execution in format
                           yyyymmddhhmmss, the string 'TIME_NOW' which
                           means execute immediately or None which means
                           the job will not execute until
                           schedule_job_execution is called
        :returns: id of the created configuration job
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the iDRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        return self._job_mgmt.create_config_job(
            resource_uri=uris.DCIM_iDRACCardService,
            cim_creation_class_name='DCIM_iDRACCardService',
            cim_name='DCIM:iDRACCardService',
            target=idrac_fqdd,
            reboot=reboot,
            start_time=start_time)

    def abandon_pending_idrac_changes(self, idrac_fqdd=IDRAC_FQDD):
        """Abandon all pending changes to an iDRAC

        Once a config job has been submitted, it can no longer be abandoned.

        :param idrac_fqdd: the FQDD of the iDRAC.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the iDRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        self._job_mgmt.delete_pending_config(
            resource_uri=uris.DCIM_iDRACCardService,
            cim_creation_class_name='DCIM_iDRACCardService',
            cim_name='DCIM:iDRACCardService',
            target=idrac_fqdd)

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

    def list_system_settings(self):
        """List the System configuration settings

        :returns: a dictionary with the System settings using its instance id
                  as key. The attributes are either SystemEnumerableAttribute,
                  SystemStringAttribute or SystemIntegerAttribute objects.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._system_cfg.list_system_settings()

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

    def delete_jobs(self, job_ids=['JID_CLEARALL']):
        """Deletes the given jobs, or all jobs if none specified

        :param job_ids: a list of job ids to delete. Clearing all the
                jobs may be accomplished using the keyword JID_CLEARALL
                as the job_id, or JID_CLEARALL_FORCE if a job is in
                Scheduled state and there is another job for the same
                component in Completed or Failed state,
                (http://en.community.dell.com/techcenter/extras/m/white_papers/20444501/download)
                Deletion of each job id will be attempted, even if there
                are errors in deleting any in the list.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the iDRAC
                 interface.  There will be one message for each job_id
                 that had a failure in the exception.
        :raises: DRACUnexpectedReturnValue on non-success
        """

        return self._job_mgmt.delete_jobs(job_ids)

    def create_config_job(self,
                          resource_uri,
                          cim_creation_class_name,
                          cim_name,
                          target,
                          cim_system_creation_class_name='DCIM_ComputerSystem',
                          cim_system_name='DCIM:ComputerSystem',
                          reboot=False,
                          start_time='TIME_NOW',
                          realtime=False):
        """Creates a configuration job.

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
        :param reboot: indicates whether or not a RebootJob should also be
                       created
        :param start_time: start time for job execution in format
                           yyyymmddhhmmss, the string 'TIME_NOW' which
                           means execute immediately or None which means
                           the job will not execute until
                           schedule_job_execution is called
        :param realtime: Indicates if reatime mode should be used.
               Valid values are True and False.
        :returns: id of the created job
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the iDRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """

        return self._job_mgmt.create_config_job(
            resource_uri=resource_uri,
            cim_creation_class_name=cim_creation_class_name,
            cim_name=cim_name,
            target=target,
            cim_system_creation_class_name=cim_system_creation_class_name,
            cim_system_name=cim_system_name,
            reboot=reboot,
            start_time=start_time,
            realtime=realtime)

    def create_nic_config_job(
            self,
            nic_id,
            reboot=False,
            start_time='TIME_NOW'):
        """Creates config job for applying pending changes to a NIC.

        :param nic_id: id of the network interface controller (NIC)
        :param reboot: indication of whether to also create a reboot job
        :param start_time: start time for job execution in format
                           yyyymmddhhmmss; the string 'TIME_NOW' means
                           immediately and None means unspecified
        :returns: id of the created configuration job
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the iDRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        return self._job_mgmt.create_config_job(
            resource_uri=uris.DCIM_NICService,
            cim_creation_class_name='DCIM_NICService',
            cim_name='DCIM:NICService',
            target=nic_id,
            reboot=reboot,
            start_time=start_time)

    def create_reboot_job(
            self,
            reboot_type=constants.RebootJobType.reboot_forced_shutdown):
        """Creates a reboot job.

        :param reboot_type: type of reboot
        :returns id of the created job
        :raises: InvalidParameterValue on invalid reboot type
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the iDRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        return self._job_mgmt.create_reboot_job(reboot_type)

    def schedule_job_execution(self, job_ids, start_time='TIME_NOW'):
        """Schedules jobs for execution in a specified order.

        :param job_ids: list of job identifiers
        :param start_time: start time for job execution in format
                           yyyymmddhhmmss or the string 'TIME_NOW' which
                           means execute immediately.  None is not a
                           valid option for this request.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the iDRAC
                 interface, including start_time being in the past or
                 badly formatted start_time
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        return self._job_mgmt.schedule_job_execution(job_ids, start_time)

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

    def commit_pending_bios_changes(
            self,
            reboot=False,
            start_time='TIME_NOW'):
        """Applies all pending changes on the BIOS by creating a config job

        :param reboot: indicates whether a RebootJob should also be
                       created or not
        :param start_time: start time for job execution in format
                           yyyymmddhhmmss, the string 'TIME_NOW' which
                           means execute immediately or None which means
                           the job will not execute until
                           schedule_job_execution is called
        :returns: id of the created job
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface, including start_time being in the past or
                 badly formatted start_time
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        return self._job_mgmt.create_config_job(
            resource_uri=uris.DCIM_BIOSService,
            cim_creation_class_name='DCIM_BIOSService',
            cim_name='DCIM:BIOSService',
            target=self.BIOS_DEVICE_FQDD,
            reboot=reboot,
            start_time=start_time)

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
        :returns: a dictionary containing:
                 - The is_commit_required key with the value always set to
                   True indicating that a config job must be created to
                   complete disk conversion.
                 - The is_reboot_required key with a RebootRequired enumerated
                   value indicating whether the server must be rebooted to
                   complete disk conversion.
        """
        return self._raid_mgmt.convert_physical_disks(physical_disks,
                                                      raid_enable)

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
        :returns: a dictionary containing:
                 - The is_commit_required key with the value always set to
                   True indicating that a config job must be created to
                   complete virtual disk creation.
                 - The is_reboot_required key with a RebootRequired enumerated
                   value indicating whether the server must be rebooted to
                   complete virtual disk creation.
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
        :returns: a dictionary containing:
                 - The is_commit_required key with the value always set to
                   True indicating that a config job must be created to
                   complete virtual disk deletion.
                 - The is_reboot_required key with a RebootRequired enumerated
                   value indicating whether the server must be rebooted to
                   complete virtual disk deletion.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        return self._raid_mgmt.delete_virtual_disk(virtual_disk)

    def commit_pending_raid_changes(self, raid_controller, reboot=False,
                                    start_time='TIME_NOW', realtime=False):
        """Applies all pending changes on a RAID controller

         ...by creating a config job.

        :param raid_controller: id of the RAID controller
        :param reboot: indicates whether a RebootJob should also be
                       created or not
        :param start_time: start time for job execution in format
               yyyymmddhhmmss, the string 'TIME_NOW' which
               means execute immediately or None which means
               the job will not execute until
               schedule_job_execution is called
        :param realtime: Indicates if reatime mode should be used.
               Valid values are True and False.
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
            cim_name='DCIM:RAIDService',
            target=raid_controller,
            reboot=reboot,
            start_time=start_time,
            realtime=realtime)

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

    def is_realtime_supported(self, raid_controller):
        """Find if controller supports realtime or not

        :param raid_controller: ID of RAID controller
        :returns: True or False
        """
        return self._raid_mgmt.is_realtime_supported(raid_controller)

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

    def list_nics(self, sort=False):
        """Returns a list of NICs

        :param sort: indicates if the list should be sorted or not.
        :returns: a list of NIC objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        return self._inventory_mgmt.list_nics(sort=sort)

    def list_nic_settings(self, nic_id):
        """Return the list of attribute settings of a NIC.

        :param nic_id: id of the network interface controller (NIC)
        :returns: dictionary containing the NIC settings. The keys are
                  attribute names. Each value is a
                  NICEnumerationAttribute, NICIntegerAttribute, or
                  NICStringAttribute object.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the iDRAC
                 interface
        """
        return self._nic_cfg.list_nic_settings(nic_id)

    def set_nic_settings(self, nic_id, settings):
        """Modify one or more settings of a NIC.

        If successful, the pending values of the attributes are set. For
        the new values to be applied, a configuration job must be
        created and the node must be rebooted.

        :param nic_id: id of the network interface controller (NIC)
        :param settings: dictionary containing the proposed values, with
                         each key being the name of an attribute and the
                         value being the proposed value
        :returns: dictionary containing:
                  - The is_commit_required key with a boolean value
                    indicating whether a config job must be created for
                    the values to be applied.
                  - The is_reboot_required key with a RebootRequired
                    enumerated value indicating whether the server must
                    be rebooted for the values to be applied.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the iDRAC
                 interface
        :raises: InvalidParameterValue on invalid NIC attribute
        """
        return self._nic_cfg.set_nic_settings(nic_id, settings)

    def get_system(self):
        """Return a Systen object.

        :returns: a System object
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        """
        return self._inventory_mgmt.get_system()

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

        return self.client.is_idrac_ready()

    def wait_until_idrac_is_ready(self, retries=None, retry_delay=None):
        """Waits until the iDRAC is in a ready state

        :param retries: The number of times to check if the iDRAC is
                        ready. If None, the value of ready_retries that
                        was provided when the object was created is
                        used.
        :param retry_delay: The number of seconds to wait between
                            retries. If None, the value of
                            ready_retry_delay that was provided
                            when the object was created is used.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface or timeout
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """

        return self.client.wait_until_idrac_is_ready(retries, retry_delay)

    def is_jbod_capable(self, raid_controller_fqdd):
        """Find out if raid controller supports jbod

        :param raid_controller_fqdd: The raid controller's fqdd
                                     being checked to see if it is jbod
                                     capable.
        :raises: DRACRequestFailed if unable to find any disks in the Ready
                 or non-RAID states
        :raises: DRACOperationFailed on error reported back by the DRAC
                 and the exception message does not contain
                 NOT_SUPPORTED_MSG constant
        """
        return self._raid_mgmt.is_jbod_capable(raid_controller_fqdd)

    def is_raid_controller(self, raid_controller_fqdd):
        """Find out if object's fqdd is for a raid controller or not

        :param raid_controller_fqdd: The object's fqdd we are testing to see
                                     if it is a raid controller or not.
        :returns: boolean, True if the device is a RAID controller,
                  False if not.
        """
        return self._raid_mgmt.is_raid_controller(raid_controller_fqdd)

    def is_boss_controller(self, raid_controller_fqdd, raid_controllers=None):
        """Find out if a RAID controller a BOSS card or not

        :param raid_controller_fqdd: The object's fqdd we are testing to see
                                     if it is a BOSS card or not.
        :param raid_controllers: A list of RAIDController to scan for presence
                                 of BOSS card, if None the drac will be queried
                                 for the list of controllers which will then be
                                 scanned.
        :returns: boolean, True if the device is a BOSS card, False if not.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._raid_mgmt.is_boss_controller(raid_controller_fqdd,
                                                  raid_controllers)

    def change_physical_disk_state(self, mode,
                                   controllers_to_physical_disk_ids=None):
        """Convert disks RAID status and return a list of controller IDs

        Builds a list of controller ids that have had disks converted to the
        specified RAID status by:
        - Examining all the disks in the system and filtering out any that are
          not attached to a RAID/BOSS controller.
        - Inspect the controllers' disks to see if there are any that need to
          be converted, if so convert them. If a disk is already in the desired
          status the disk is ignored. Also check for failed or unknown disk
          statuses and raise an exception where appropriate.
        - Return a list of controller IDs for controllers whom have had any of
          their disks converted, and whether a reboot is required.

        The caller typically should then create a config job for the list of
        controllers returned to finalize the RAID configuration.

        :param mode: constants.RaidStatus enumeration used to determine what
                     raid status to check for.
        :param controllers_to_physical_disk_ids: Dictionary of controllers and
               corresponding disk ids we are inspecting and creating jobs for
               when needed.
        :returns: a dict containing the following key/values:
                  - is_reboot_required, a boolean stating whether a reboot is
                  required or not.
                  - commit_required_ids, a list of controller ids that will
                  need to commit their pending RAID changes via a config job.
        :raises: DRACOperationFailed on error reported back by the DRAC and the
                 exception message does not contain NOT_SUPPORTED_MSG constant.
        :raises: Exception on unknown error.
        """
        return (self._raid_mgmt
                .change_physical_disk_state(mode,
                                            controllers_to_physical_disk_ids))


class WSManClient(wsman.Client):
    """Wrapper for wsman.Client that can wait until iDRAC is ready

       Additionally, the Invoke operation offers return value checking.
    """

    def __init__(
            self, host, username, password, port=443, path='/wsman',
            protocol='https',
            ssl_retries=constants.DEFAULT_WSMAN_SSL_ERROR_RETRIES,
            ssl_retry_delay=constants.DEFAULT_WSMAN_SSL_ERROR_RETRY_DELAY_SEC,
            ready_retries=constants.DEFAULT_IDRAC_IS_READY_RETRIES,
            ready_retry_delay=(
                constants.DEFAULT_IDRAC_IS_READY_RETRY_DELAY_SEC)):
        """Creates client object

        :param host: hostname or IP of the DRAC interface
        :param username: username for accessing the DRAC interface
        :param password: password for accessing the DRAC interface
        :param port: port for accessing the DRAC interface
        :param path: path for accessing the DRAC interface
        :param protocol: protocol for accessing the DRAC interface
        :param ssl_retries: number of resends to attempt on SSL failures
        :param ssl_retry_delay: number of seconds to wait between
                                retries on SSL failures
        :param ready_retries: number of times to check if the iDRAC is
                              ready
        :param ready_retry_delay: number of seconds to wait between
                                  checks if the iDRAC is ready
        """
        super(WSManClient, self).__init__(host, username, password,
                                          port, path, protocol, ssl_retries,
                                          ssl_retry_delay)

        self._ready_retries = ready_retries
        self._ready_retry_delay = ready_retry_delay

    def enumerate(self, resource_uri, optimization=True, max_elems=100,
                  auto_pull=True, filter_query=None, filter_dialect='cql',
                  wait_for_idrac=True):
        """Executes enumerate operation over WS-Man

        :param resource_uri: URI of resource to enumerate
        :param optimization: flag to enable enumeration optimization. If
                             disabled, the enumeration returns only an
                             enumeration context.
        :param max_elems: maximum number of elements returned by the operation
        :param auto_pull: flag to enable automatic pull on the enumeration
                          context, merging the items returned
        :param filter_query: filter query string
        :param filter_dialect: filter dialect. Valid options are: 'cql' and
                               'wql'.
        :param wait_for_idrac: indicates whether or not to wait for the
            iDRAC to be ready to accept commands before issuing the
            command
        :returns: an lxml.etree.Element object of the response received
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        """
        if wait_for_idrac:
            self.wait_until_idrac_is_ready()

        return super(WSManClient, self).enumerate(resource_uri, optimization,
                                                  max_elems, auto_pull,
                                                  filter_query, filter_dialect)

    def invoke(self,
               resource_uri,
               method,
               selectors=None,
               properties=None,
               expected_return_value=None,
               wait_for_idrac=True,
               check_return_value=True):
        """Invokes a remote WS-Man method

        :param resource_uri: URI of the resource
        :param method: name of the method to invoke
        :param selectors: dictionary of selectors
        :param properties: dictionary of properties
        :param expected_return_value: expected return value reported back by
            the DRAC card. For return value codes check the profile
            documentation of the resource used in the method call. If not set,
            return value checking is skipped.
        :param wait_for_idrac: indicates whether or not to wait for the
            iDRAC to be ready to accept commands before issuing the
            command
        :param check_return_value: indicates if the ReturnValue should be
            checked and an exception thrown on an unexpected value
        :returns: an lxml.etree.Element object of the response received
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        if wait_for_idrac:
            self.wait_until_idrac_is_ready()

        if selectors is None:
            selectors = {}

        if properties is None:
            properties = {}

        resp = super(WSManClient, self).invoke(resource_uri, method, selectors,
                                               properties)

        if check_return_value:
            return_value = utils.find_xml(resp, 'ReturnValue',
                                          resource_uri).text
            if return_value == utils.RET_ERROR:
                message_elems = utils.find_xml(resp, 'Message',
                                               resource_uri, True)
                messages = [message_elem.text for message_elem in
                            message_elems]
                raise exceptions.DRACOperationFailed(drac_messages=messages)

            if (expected_return_value is not None
                    and return_value != expected_return_value):
                raise exceptions.DRACUnexpectedReturnValue(
                    expected_return_value=expected_return_value,
                    actual_return_value=return_value)

        return resp

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

        selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                     'SystemName': 'DCIM:ComputerSystem',
                     'CreationClassName': 'DCIM_LCService',
                     'Name': 'DCIM:LCService'}

        result = self.invoke(uris.DCIM_LCService,
                             'GetRemoteServicesAPIStatus',
                             selectors,
                             {},
                             expected_return_value=utils.RET_SUCCESS,
                             wait_for_idrac=False)

        message_id = utils.find_xml(result,
                                    'MessageID',
                                    uris.DCIM_LCService).text

        return message_id == IDRAC_IS_READY

    def wait_until_idrac_is_ready(self, retries=None, retry_delay=None):
        """Waits until the iDRAC is in a ready state

        :param retries: The number of times to check if the iDRAC is
                        ready. If None, the value of ready_retries that
                        was provided when the object was created is
                        used.
        :param retry_delay: The number of seconds to wait between
                            retries. If None, the value of
                            ready_retry_delay that was provided when the
                            object was created is used.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface or timeout
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """

        if retries is None:
            retries = self._ready_retries

        if retry_delay is None:
            retry_delay = self._ready_retry_delay

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
