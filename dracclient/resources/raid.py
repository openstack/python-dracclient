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

import collections
import logging

from dracclient import constants
from dracclient import exceptions
from dracclient.resources import uris
from dracclient import utils

LOG = logging.getLogger(__name__)

RAID_LEVELS = {
    'non-raid': '1',
    '0': '2',
    '1': '4',
    '5': '64',
    '6': '128',
    '1+0': '2048',
    '5+0': '8192',
    '6+0': '16384',
}

REVERSE_RAID_LEVELS = dict((v, k) for (k, v) in RAID_LEVELS.items())

RAID_CONTROLLER_IS_REALTIME = {
    '1': True,
    '0': False
}

DISK_RAID_STATUS = {
    '0': 'unknown',
    '1': 'ready',
    '2': 'online',
    '3': 'foreign',
    '4': 'offline',
    '5': 'blocked',
    '6': 'failed',
    '7': 'degraded',
    '8': 'non-RAID',
    '9': 'missing'
}

VIRTUAL_DISK_PENDING_OPERATIONS = {
    '0': None,
    '1': 'fast_init',
    '2': 'pending_delete',
    '3': 'pending_create'
}

PHYSICAL_DISK_MEDIA_TYPE = {
    '0': 'hdd',
    '1': 'ssd'
}

PHYSICAL_DISK_BUS_PROTOCOL = {
    '0': 'unknown',
    '1': 'scsi',
    '2': 'pata',
    '3': 'fibre',
    '4': 'usb',
    '5': 'sata',
    '6': 'sas',
    '7': 'pcie',
    '8': 'nvme'
}

PhysicalDisk = collections.namedtuple(
    'PhysicalDisk',
    ['id', 'description', 'controller', 'manufacturer', 'model', 'media_type',
     'interface_type', 'size_mb', 'free_size_mb', 'serial_number',
     'firmware_version', 'status', 'raid_status', 'sas_address',
     'device_protocol'])

RAIDController = collections.namedtuple(
    'RAIDController', ['id', 'description', 'manufacturer', 'model',
                       'primary_status', 'firmware_version', 'bus',
                       'supports_realtime'])

VirtualDisk = collections.namedtuple(
    'VirtualDisk',
    ['id', 'name', 'description', 'controller', 'raid_level', 'size_mb',
     'status', 'raid_status', 'span_depth', 'span_length',
     'pending_operations', 'physical_disks'])


class RAIDManagement(object):

    def __init__(self, client):
        """Creates RAIDManagement object

        :param client: an instance of WSManClient
        """
        self.client = client

    def list_raid_controllers(self):
        """Returns the list of RAID controllers

        :returns: a list of RAIDController objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        doc = self.client.enumerate(uris.DCIM_ControllerView)

        drac_raid_controllers = utils.find_xml(doc, 'DCIM_ControllerView',
                                               uris.DCIM_ControllerView,
                                               find_all=True)

        return [self._parse_drac_raid_controller(controller)
                for controller in drac_raid_controllers]

    def _parse_drac_raid_controller(self, drac_controller):
        return RAIDController(
            id=self._get_raid_controller_attr(drac_controller, 'FQDD'),
            description=self._get_raid_controller_attr(
                drac_controller, 'DeviceDescription'),
            manufacturer=self._get_raid_controller_attr(
                drac_controller, 'DeviceCardManufacturer'),
            model=self._get_raid_controller_attr(
                drac_controller, 'ProductName'),
            primary_status=constants.PRIMARY_STATUS[
                self._get_raid_controller_attr(drac_controller,
                                               'PrimaryStatus')],
            firmware_version=self._get_raid_controller_attr(
                drac_controller, 'ControllerFirmwareVersion'),
            bus=self._get_raid_controller_attr(drac_controller, 'Bus'),
            supports_realtime=RAID_CONTROLLER_IS_REALTIME[
                self._get_raid_controller_attr(
                    drac_controller, 'RealtimeCapability')])

    def _get_raid_controller_attr(self, drac_controller, attr_name):
        return utils.get_wsman_resource_attr(
            drac_controller, uris.DCIM_ControllerView, attr_name,
            nullable=True)

    def list_virtual_disks(self):
        """Returns the list of virtual disks

        :returns: a list of VirtualDisk objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        doc = self.client.enumerate(uris.DCIM_VirtualDiskView)

        drac_virtual_disks = utils.find_xml(doc, 'DCIM_VirtualDiskView',
                                            uris.DCIM_VirtualDiskView,
                                            find_all=True)

        return [self._parse_drac_virtual_disk(disk)
                for disk in drac_virtual_disks]

    def _parse_drac_virtual_disk(self, drac_disk):
        fqdd = self._get_virtual_disk_attr(drac_disk, 'FQDD')
        drac_raid_level = self._get_virtual_disk_attr(drac_disk, 'RAIDTypes')
        size_b = self._get_virtual_disk_attr(drac_disk, 'SizeInBytes')
        drac_status = self._get_virtual_disk_attr(drac_disk, 'PrimaryStatus')
        drac_raid_status = self._get_virtual_disk_attr(drac_disk, 'RAIDStatus')
        drac_pending_operations = self._get_virtual_disk_attr(
            drac_disk, 'PendingOperations')

        return VirtualDisk(
            id=fqdd,
            name=self._get_virtual_disk_attr(drac_disk, 'Name',
                                             nullable=True),
            description=self._get_virtual_disk_attr(drac_disk,
                                                    'DeviceDescription',
                                                    nullable=True),
            controller=fqdd.split(':')[-1],
            raid_level=REVERSE_RAID_LEVELS[drac_raid_level],
            size_mb=int(size_b) // 2 ** 20,
            status=constants.PRIMARY_STATUS[drac_status],
            raid_status=DISK_RAID_STATUS[drac_raid_status],
            span_depth=int(self._get_virtual_disk_attr(drac_disk,
                                                       'SpanDepth')),
            span_length=int(self._get_virtual_disk_attr(drac_disk,
                                                        'SpanLength')),
            pending_operations=(
                VIRTUAL_DISK_PENDING_OPERATIONS[drac_pending_operations]),
            physical_disks=self._get_virtual_disk_attrs(drac_disk,
                                                        'PhysicalDiskIDs'))

    def _get_virtual_disk_attr(self, drac_disk, attr_name, nullable=False):
        return utils.get_wsman_resource_attr(
            drac_disk, uris.DCIM_VirtualDiskView, attr_name,
            nullable=nullable)

    def _get_virtual_disk_attrs(self, drac_disk, attr_name):
        return utils.get_all_wsman_resource_attrs(
            drac_disk, uris.DCIM_VirtualDiskView, attr_name, nullable=False)

    def list_physical_disks(self):
        """Returns the list of physical disks

        :returns: a list of PhysicalDisk objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        doc = self.client.enumerate(uris.DCIM_PhysicalDiskView)

        drac_physical_disks = utils.find_xml(doc, 'DCIM_PhysicalDiskView',
                                             uris.DCIM_PhysicalDiskView,
                                             find_all=True)
        physical_disks = [self._parse_drac_physical_disk(disk)
                          for disk in drac_physical_disks]

        drac_pcie_disks = utils.find_xml(doc, 'DCIM_PCIeSSDView',
                                         uris.DCIM_PCIeSSDView,
                                         find_all=True)
        pcie_disks = [self._parse_drac_physical_disk(disk,
                      uris.DCIM_PCIeSSDView) for disk in drac_pcie_disks]

        return physical_disks + pcie_disks

    def _parse_drac_physical_disk(self,
                                  drac_disk,
                                  uri=uris.DCIM_PhysicalDiskView):
        fqdd = self._get_physical_disk_attr(drac_disk, 'FQDD', uri)
        size_b = self._get_physical_disk_attr(drac_disk, 'SizeInBytes', uri)

        free_size_b = self._get_physical_disk_attr(drac_disk,
                                                   'FreeSizeInBytes', uri)
        if free_size_b is not None:
            free_size_mb = int(free_size_b) // 2 ** 20
        else:
            free_size_mb = None

        drac_status = self._get_physical_disk_attr(drac_disk, 'PrimaryStatus',
                                                   uri)
        drac_raid_status = self._get_physical_disk_attr(drac_disk,
                                                        'RaidStatus', uri)
        if drac_raid_status is not None:
            raid_status = DISK_RAID_STATUS[drac_raid_status]
        else:
            raid_status = None
        drac_media_type = self._get_physical_disk_attr(drac_disk, 'MediaType',
                                                       uri)
        drac_bus_protocol = self._get_physical_disk_attr(drac_disk,
                                                         'BusProtocol', uri)

        return PhysicalDisk(
            id=fqdd,
            description=self._get_physical_disk_attr(drac_disk,
                                                     'DeviceDescription',
                                                     uri),
            controller=fqdd.split(':')[-1],
            manufacturer=self._get_physical_disk_attr(drac_disk,
                                                      'Manufacturer', uri),
            model=self._get_physical_disk_attr(drac_disk, 'Model', uri),
            media_type=PHYSICAL_DISK_MEDIA_TYPE[drac_media_type],
            interface_type=PHYSICAL_DISK_BUS_PROTOCOL[drac_bus_protocol],
            size_mb=int(size_b) // 2 ** 20,
            free_size_mb=free_size_mb,
            serial_number=self._get_physical_disk_attr(drac_disk,
                                                       'SerialNumber', uri),
            firmware_version=self._get_physical_disk_attr(drac_disk,
                                                          'Revision', uri),
            status=constants.PRIMARY_STATUS[drac_status],
            raid_status=raid_status,
            sas_address=self._get_physical_disk_attr(drac_disk, 'SASAddress',
                                                     uri, allow_missing=True),
            device_protocol=self._get_physical_disk_attr(drac_disk,
                                                         'DeviceProtocol',
                                                         uri,
                                                         allow_missing=True))

    def _get_physical_disk_attr(self, drac_disk, attr_name, uri,
                                allow_missing=False):
        return utils.get_wsman_resource_attr(
            drac_disk, uri, attr_name, nullable=True,
            allow_missing=allow_missing)

    def convert_physical_disks(self, physical_disks, raid_enable):
        """Converts a list of physical disks into or out of RAID mode.

        Disks can be enabled or disabled for RAID mode.

        :param physical_disks: list of FQDD ID strings of the physical disks
                               to update
        :param raid_enable: boolean flag, set to True if the disk is to
                            become part of the RAID.  The same flag is applied
                            to all listed disks
        :returns: a dictionary containing:
                 - The is_commit_required key with the value always set to
                   True indicating that a config job must be created to
                   complete disk conversion.
                 - The is_reboot_required key with a RebootRequired enumerated
                   value indicating whether the server must be rebooted to
                   complete disk conversion.
        """
        invocation = 'ConvertToRAID' if raid_enable else 'ConvertToNonRAID'

        selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                     'CreationClassName': 'DCIM_RAIDService',
                     'SystemName': 'DCIM:ComputerSystem',
                     'Name': 'DCIM:RAIDService'}

        properties = {'PDArray': physical_disks}

        doc = self.client.invoke(uris.DCIM_RAIDService, invocation,
                                 selectors, properties,
                                 expected_return_value=utils.RET_SUCCESS)

        return utils.build_return_dict(doc, uris.DCIM_RAIDService,
                                       is_commit_required_value=True)

    def create_virtual_disk(self, raid_controller, physical_disks, raid_level,
                            size_mb, disk_name=None, span_length=None,
                            span_depth=None):
        """Creates a virtual disk

        The created virtual disk will be in pending state. For the changes to
        be applied, a config job must be created and the node must be rebooted.

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

        virtual_disk_prop_names = []
        virtual_disk_prop_values = []
        error_msgs = []

        # RAID controller validation
        if not raid_controller:
            error_msgs.append("'raid_controller' is not supplied")

        # physical disks validation
        if not physical_disks:
            error_msgs.append("'physical_disks' is not supplied")

        # size validation
        utils.validate_integer_value(size_mb, 'size_mb', error_msgs)

        virtual_disk_prop_names.append('Size')
        virtual_disk_prop_values.append(str(size_mb))

        # RAID level validation
        virtual_disk_prop_names.append('RAIDLevel')
        try:
            virtual_disk_prop_values.append(RAID_LEVELS[str(raid_level)])
        except KeyError:
            error_msgs.append("'raid_level' is invalid")

        if disk_name is not None:
            virtual_disk_prop_names.append('VirtualDiskName')
            virtual_disk_prop_values.append(disk_name)

        if span_depth is not None:
            utils.validate_integer_value(span_depth, 'span_depth', error_msgs)

            virtual_disk_prop_names.append('SpanDepth')
            virtual_disk_prop_values.append(str(span_depth))

        if span_length is not None:
            utils.validate_integer_value(span_length, 'span_length',
                                         error_msgs)

            virtual_disk_prop_names.append('SpanLength')
            virtual_disk_prop_values.append(str(span_length))

        if error_msgs:
            msg = ('The following errors were encountered while parsing '
                   'the provided parameters: %r') % ','.join(error_msgs)
            raise exceptions.InvalidParameterValue(reason=msg)

        selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                     'CreationClassName': 'DCIM_RAIDService',
                     'SystemName': 'DCIM:ComputerSystem',
                     'Name': 'DCIM:RAIDService'}
        properties = {'Target': raid_controller,
                      'PDArray': physical_disks,
                      'VDPropNameArray': virtual_disk_prop_names,
                      'VDPropValueArray': virtual_disk_prop_values}
        doc = self.client.invoke(uris.DCIM_RAIDService, 'CreateVirtualDisk',
                                 selectors, properties,
                                 expected_return_value=utils.RET_SUCCESS)

        return utils.build_return_dict(doc, uris.DCIM_RAIDService,
                                       is_commit_required_value=True)

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

        selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                     'CreationClassName': 'DCIM_RAIDService',
                     'SystemName': 'DCIM:ComputerSystem',
                     'Name': 'DCIM:RAIDService'}
        properties = {'Target': virtual_disk}

        doc = self.client.invoke(uris.DCIM_RAIDService, 'DeleteVirtualDisk',
                                 selectors, properties,
                                 expected_return_value=utils.RET_SUCCESS)

        return utils.build_return_dict(doc, uris.DCIM_RAIDService,
                                       is_commit_required_value=True)

    def is_jbod_capable(self, raid_controller_fqdd):
        """Find out if raid controller supports jbod

        :param raid_controller_fqdd: The raid controller's fqdd
                        being being checked to see if it is jbod
                        capable.
        :raises: DRACRequestFailed if unable to find any disks in the Ready
                 or non-RAID states
        :raises: DRACOperationFailed on error reported back by the DRAC
                 and the exception message does not contain
                 NOT_SUPPORTED_MSG constant
        """
        is_jbod_capable = False

        # Grab all the disks associated with the RAID controller
        all_physical_disks = self.list_physical_disks()
        physical_disks = [physical_disk for physical_disk in all_physical_disks
                          if physical_disk.controller == raid_controller_fqdd]

        # If there is a disk in the Non-RAID state, then the controller is JBOD
        # capable
        ready_disk = None
        for physical_disk in physical_disks:
            if physical_disk.raid_status == 'non-RAID':
                is_jbod_capable = True
                break
            elif not ready_disk and physical_disk.raid_status == 'ready':
                ready_disk = physical_disk

        if not is_jbod_capable:
            if not ready_disk:
                msg = "Unable to find a disk in the Ready state"
                raise exceptions.DRACRequestFailed(msg)

            # Try moving a disk in the Ready state to JBOD mode
            try:
                self.convert_physical_disks([ready_disk.id], False)
                is_jbod_capable = True

                # Flip the disk back to the Ready state.  This results in the
                # pending value being reset to nothing, so it effectively
                # undoes the last command and makes the check non-destructive
                self.convert_physical_disks([ready_disk.id], True)
            except exceptions.DRACOperationFailed as ex:
                # Fix for python 3, Exception.message no longer
                # a valid attribute, str(ex) works for both 2.7
                # and 3.x
                if constants.NOT_SUPPORTED_MSG in str(ex):
                    pass
                else:
                    raise

        return is_jbod_capable

    def is_raid_controller(self, raid_controller_fqdd):
        """Find out if object's fqdd is for a raid controller or not

        :param raid_controller_fqdd: The object's fqdd we are testing to see
                                     if it is a raid controller or not.
        :returns: boolean, True if the device is a RAID controller,
                  False if not.
        """
        return raid_controller_fqdd.startswith('RAID.')

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
        if raid_controllers is None:
            raid_controllers = self.list_raid_controllers()
        boss_raid_controllers = [
            c.id for c in raid_controllers if c.model.startswith('BOSS')]
        return raid_controller_fqdd in boss_raid_controllers

    def _check_disks_status(self, mode, physical_disks,
                            controllers_to_physical_disk_ids):
        """Find disks that failed, need to be configured, or need no change.

        Inspect all the controllers drives and:
            - See if there are any disks in a failed or unknown state and raise
            a ValueException where appropriate.
            - If a controller has disks that still need to be configured add
            them to the controllers_to_physical_disk_ids dict for the
            appropriate controller.
            - If a disk is already in the appropriate state, do nothing, this
            function should behave in an idempotent manner.

        :param mode: constants.RaidStatus enumeration used to
                     determine what raid status to check for.
        :param physical_disks: all physical disks
        :param controllers_to_physical_disk_ids: Dictionary of controllers
                     we are inspecting and creating jobs for when needed. If
                     needed modify this dict so that only drives that need to
                     be changed to RAID or JBOD are in the list of disk keys
                     for corresponding controller.
        :raises: ValueError: Exception message will list failed drives and
                     drives whose state cannot be changed at this time, drive
                     state is not "ready" or "non-RAID".
        """
        p_disk_id_to_status = {}
        for physical_disk in physical_disks:
            p_disk_id_to_status[physical_disk.id] = physical_disk.raid_status
        failed_disks = []
        bad_disks = []

        jbod = constants.RaidStatus.jbod
        raid = constants.RaidStatus.raid
        for controller, physical_disk_ids \
                in controllers_to_physical_disk_ids.items():
            final_physical_disk_ids = []
            for physical_disk_id in physical_disk_ids:
                raid_status = p_disk_id_to_status[physical_disk_id]
                LOG.debug("RAID status for disk id: %s is: %s",
                          physical_disk_id, raid_status)
                if ((mode == jbod and raid_status == "non-RAID") or
                        (mode == raid and raid_status == "ready")):
                    # This means the disk is already in the desired state,
                    # so skip it
                    continue
                elif ((mode == jbod and raid_status == "ready") or
                        (mode == raid and raid_status == "non-RAID")):
                    # This disk is moving from a state we expect to RAID or
                    # JBOD, so keep it
                    final_physical_disk_ids.append(physical_disk_id)
                elif raid_status == "failed":
                    failed_disks.append(physical_disk_id)
                else:
                    # This disk is in one of many states that we don't know
                    # what to do with, so pitch it
                    bad_disks.append("{} ({})".format(physical_disk_id,
                                                      raid_status))

            controllers_to_physical_disk_ids[controller] = (
                final_physical_disk_ids)

        if failed_disks or bad_disks:
            error_msg = ""

            if failed_disks:
                error_msg += ("The following drives have failed: "
                              "{failed_disks}.  Manually check the status"
                              " of all drives and replace as necessary, then"
                              " try again.").format(
                                  failed_disks=" ".join(failed_disks))

            if bad_disks:
                if failed_disks:
                    error_msg += "\n"
                error_msg += ("Unable to change the state of the following "
                              "drives because their status is not ready "
                              "or non-RAID: {}. Bring up the RAID "
                              "controller GUI on this node and change the "
                              "drives' status to ready or non-RAID.").format(
                                  ", ".join(bad_disks))

            raise ValueError(error_msg)

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
        physical_disks = self.list_physical_disks()

        raid = constants.RaidStatus.raid

        if not controllers_to_physical_disk_ids:
            controllers_to_physical_disk_ids = collections.defaultdict(list)

            for physical_d in physical_disks:
                # Weed out disks that are not attached to a RAID controller
                if (self.is_raid_controller(physical_d.controller)
                        or self.is_boss_controller(physical_d.controller)):
                    physical_disk_ids = controllers_to_physical_disk_ids[
                        physical_d.controller]

                    physical_disk_ids.append(physical_d.id)

        '''Modify controllers_to_physical_disk_ids dict by inspecting desired
        status vs current status of each controller's disks.
        Raise exception if there are any failed drives or
        drives not in status 'ready' or 'non-RAID'
        '''
        self._check_disks_status(mode, physical_disks,
                                 controllers_to_physical_disk_ids)

        is_reboot_required = False
        controllers = []
        for controller, physical_disk_ids \
                in controllers_to_physical_disk_ids.items():
            if physical_disk_ids:
                LOG.debug("Converting the following disks to {} on RAID "
                          "controller {}: {}".format(
                              mode, controller, str(physical_disk_ids)))
                try:
                    conversion_results = \
                        self.convert_physical_disks(physical_disk_ids,
                                                    mode == raid)
                except exceptions.DRACOperationFailed as ex:
                    if constants.NOT_SUPPORTED_MSG in str(ex):
                        LOG.debug("Controller {} does not support "
                                  "JBOD mode".format(controller))
                        pass
                    else:
                        raise
                else:
                    if conversion_results:
                        reboot_true = constants.RebootRequired.true
                        reboot_optional = constants.RebootRequired.optional
                        _is_reboot_required = \
                            conversion_results["is_reboot_required"]
                        is_reboot_required = is_reboot_required \
                            or (_is_reboot_required
                                in [reboot_true, reboot_optional])
                        if conversion_results["is_commit_required"]:
                            controllers.append(controller)

        return {'is_reboot_required': is_reboot_required,
                'commit_required_ids': controllers}

    def is_realtime_supported(self, raid_controller_fqdd):
        """Find if controller supports realtime or not

        :param raid_controller_fqdd: ID of RAID controller
        :returns: True or False
        """
        drac_raid_controllers = self.list_raid_controllers()
        realtime_controller = [cnt.id for cnt in drac_raid_controllers
                               if cnt.supports_realtime]

        if raid_controller_fqdd in realtime_controller:
            return True

        return False
