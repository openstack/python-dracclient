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
    '6': 'sas'
}

PhysicalDiskTuple = collections.namedtuple(
    'PhysicalDisk',
    ['id', 'description', 'controller', 'manufacturer', 'model', 'media_type',
     'interface_type', 'size_mb', 'free_size_mb', 'serial_number',
     'firmware_version', 'status', 'raid_status'])


class PhysicalDisk(PhysicalDiskTuple):

    def __new__(cls, **kwargs):
        if 'state' in kwargs:
            LOG.warning('PhysicalDisk.state is deprecated. '
                        'Use PhysicalDisk.status instead.')
            kwargs['status'] = kwargs['state']
            del kwargs['state']

        if 'raid_state' in kwargs:
            LOG.warning('PhysicalDisk.raid_state is deprecated. '
                        'Use PhysicalDisk.raid_status instead.')
            kwargs['raid_status'] = kwargs['raid_state']
            del kwargs['raid_state']

        return super(PhysicalDisk, cls).__new__(cls, **kwargs)

    @property
    def state(self):
        LOG.warning('PhysicalDisk.state is deprecated. '
                    'Use PhysicalDisk.status instead.')
        return self.status

    @property
    def raid_state(self):
        LOG.warning('PhysicalDisk.raid_state is deprecated. '
                    'Use PhysicalDisk.raid_status instead.')
        return self.raid_status

RAIDController = collections.namedtuple(
    'RAIDController', ['id', 'description', 'manufacturer', 'model',
                       'primary_status', 'firmware_version'])

VirtualDiskTuple = collections.namedtuple(
    'VirtualDisk',
    ['id', 'name', 'description', 'controller', 'raid_level', 'size_mb',
     'status', 'raid_status', 'span_depth', 'span_length',
     'pending_operations', 'physical_disks'])


class VirtualDisk(VirtualDiskTuple):

    def __new__(cls, **kwargs):
        if 'state' in kwargs:
            LOG.warning('VirtualDisk.state is deprecated. '
                        'Use VirtualDisk.status instead.')
            kwargs['status'] = kwargs['state']
            del kwargs['state']

        if 'raid_state' in kwargs:
            LOG.warning('VirtualDisk.raid_state is deprecated. '
                        'Use VirtualDisk.raid_status instead.')
            kwargs['raid_status'] = kwargs['raid_state']
            del kwargs['raid_state']

        return super(VirtualDisk, cls).__new__(cls, **kwargs)

    @property
    def state(self):
        LOG.warning('VirtualDisk.state is deprecated. '
                    'Use VirtualDisk.status instead.')
        return self.status

    @property
    def raid_state(self):
        LOG.warning('VirtualDisk.raid_state is deprecated. '
                    'Use VirtualDisk.raid_status instead.')
        return self.raid_status


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
                drac_controller, 'ControllerFirmwareVersion'))

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
            size_mb=int(size_b) / 2 ** 20,
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

        return [self._parse_drac_physical_disk(disk)
                for disk in drac_physical_disks]

    def _parse_drac_physical_disk(self, drac_disk):
        fqdd = self._get_physical_disk_attr(drac_disk, 'FQDD')
        size_b = self._get_physical_disk_attr(drac_disk, 'SizeInBytes')
        free_size_b = self._get_physical_disk_attr(drac_disk,
                                                   'FreeSizeInBytes')
        drac_status = self._get_physical_disk_attr(drac_disk, 'PrimaryStatus')
        drac_raid_status = self._get_physical_disk_attr(drac_disk,
                                                        'RaidStatus')
        drac_media_type = self._get_physical_disk_attr(drac_disk, 'MediaType')
        drac_bus_protocol = self._get_physical_disk_attr(drac_disk,
                                                         'BusProtocol')

        return PhysicalDisk(
            id=fqdd,
            description=self._get_physical_disk_attr(drac_disk,
                                                     'DeviceDescription'),
            controller=fqdd.split(':')[-1],
            manufacturer=self._get_physical_disk_attr(drac_disk,
                                                      'Manufacturer'),
            model=self._get_physical_disk_attr(drac_disk, 'Model'),
            media_type=PHYSICAL_DISK_MEDIA_TYPE[drac_media_type],
            interface_type=PHYSICAL_DISK_BUS_PROTOCOL[drac_bus_protocol],
            size_mb=int(size_b) / 2 ** 20,
            free_size_mb=int(free_size_b) / 2 ** 20,
            serial_number=self._get_physical_disk_attr(drac_disk,
                                                       'SerialNumber'),
            firmware_version=self._get_physical_disk_attr(drac_disk,
                                                          'Revision'),
            status=constants.PRIMARY_STATUS[drac_status],
            raid_status=DISK_RAID_STATUS[drac_raid_status])

    def _get_physical_disk_attr(self, drac_disk, attr_name):
        return utils.get_wsman_resource_attr(
            drac_disk, uris.DCIM_PhysicalDiskView, attr_name, nullable=True)

    def convert_physical_disks(self, physical_disks, raid_enable):
        """Converts a list of physical disks into or out of RAID mode.

        Disks can be enabled or disabled for RAID mode.

        :param physical_disks: list of FQDD ID strings of the physical disks
               to update
        :param raid_enable: boolean flag, set to True if the disk is to
               become part of the RAID.  The same flag is applied to all
               listed disks
        :returns: a dictionary containing the commit_needed key with a boolean
                  value indicating whether a config job must be created for the
                  values to be applied.
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

        return {'commit_required':
                utils.is_reboot_required(doc, uris.DCIM_RAIDService)}

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
        if not size_mb:
            error_msgs.append("'size_mb' is not supplied")
        else:
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

        return {'commit_required': utils.is_reboot_required(
            doc, uris.DCIM_RAIDService)}

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

        selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                     'CreationClassName': 'DCIM_RAIDService',
                     'SystemName': 'DCIM:ComputerSystem',
                     'Name': 'DCIM:RAIDService'}
        properties = {'Target': virtual_disk}

        doc = self.client.invoke(uris.DCIM_RAIDService, 'DeleteVirtualDisk',
                                 selectors, properties,
                                 expected_return_value=utils.RET_SUCCESS)

        return {'commit_required': utils.is_reboot_required(
            doc, uris.DCIM_RAIDService)}
