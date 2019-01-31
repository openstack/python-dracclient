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
import lxml.etree
import mock
import random
import requests_mock

import dracclient.client
from dracclient import constants
from dracclient import exceptions
import dracclient.resources.job
from dracclient.resources import raid
from dracclient.resources import uris
from dracclient.tests import base
from dracclient.tests import utils as test_utils
from dracclient import utils


@requests_mock.Mocker()
class ClientRAIDManagementTestCase(base.BaseTest):

    def setUp(self):
        super(ClientRAIDManagementTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)
        self.raid_controller_fqdd = "RAID.Integrated.1-1"
        cntl_dict = {'RAID.Integrated.1-1':
                     ['Disk.Bay.0:Enclosure.Internal.0-1:RAID.Integrated.1-1',
                      'Disk.Bay.1:Enclosure.Internal.0-1:RAID.Integrated.1-1'],
                     'AHCI.Integrated.1-1':
                     ['Disk.Bay.0:Enclosure.Internal.0-1:AHCI.Integrated.1-1',
                      'Disk.Bay.1:Enclosure.Internal.0-1:AHCI.Integrated.1-1']}
        self.controllers_to_physical_disk_ids = cntl_dict
        self.disk_1 = raid.PhysicalDisk(
            id='Disk.Bay.0:Enclosure.Internal.0-1:RAID.Integrated.1-1',
            description='Disk 0 in Backplane 1 of Int RAID Controller 1',
            controller='RAID.Integrated.1-1',
            manufacturer='ATA',
            model='ST91000640NS',
            media_type='hdd',
            interface_type='sata',
            size_mb=953344,
            free_size_mb=953344,
            serial_number='9XG4SLGZ',
            firmware_version='AA09',
            status='ok',
            raid_status='ready',
            sas_address='500056B37789ABE3',
            device_protocol=None)

        self.disk_2 = raid.PhysicalDisk(
            id='Disk.Bay.1:Enclosure.Internal.0-1:RAID.Integrated.1-1',
            description='Disk 1 in Backplane 1 of Int RAID Controller 1',
            controller='RAID.Integrated.1-1',
            manufacturer='ATA',
            model='ST91000640NS',
            media_type='hdd',
            interface_type='sata',
            size_mb=953344,
            free_size_mb=953344,
            serial_number='9XG4SLGZ',
            firmware_version='AA09',
            status='online',
            raid_status='ready',
            sas_address='500056B37789ABE3',
            device_protocol=None)

        self.disk_3 = raid.PhysicalDisk(
            id='Disk.Bay.0:Enclosure.Internal.0-1:AHCI.Integrated.1-1',
            description='Disk 1 in Backplane 1 of Int BOSS Controller 1',
            controller='AHCI.Integrated.1-1',
            manufacturer='ATA',
            model='ST91000640NS',
            media_type='hdd',
            interface_type='sata',
            size_mb=953344,
            free_size_mb=953344,
            serial_number='9XG4SLGZ',
            firmware_version='AA09',
            status='online',
            raid_status='ready',
            sas_address='500056B37789ABE3',
            device_protocol=None)

        self.disk_4 = raid.PhysicalDisk(
            id='Disk.Bay.1:Enclosure.Internal.0-1:AHCI.Integrated.1-1',
            description='Disk 1 in Backplane 1 of Int RAID Controller 1',
            controller='AHCI.Integrated.1-1',
            manufacturer='ATA',
            model='ST91000640NS',
            media_type='hdd',
            interface_type='sata',
            size_mb=953344,
            free_size_mb=953344,
            serial_number='9XG4SLGZ',
            firmware_version='AA09',
            status='online',
            raid_status='ready',
            sas_address='500056B37789ABE3',
            device_protocol=None)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_list_raid_controllers(self, mock_requests,
                                   mock_wait_until_idrac_is_ready):
        expected_raid_controller = raid.RAIDController(
            id='RAID.Integrated.1-1',
            description='Integrated RAID Controller 1',
            manufacturer='DELL',
            model='PERC H710 Mini',
            primary_status='ok',
            firmware_version='21.3.0-0009',
            bus='1',
            supports_realtime=True)
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_ControllerView]['ok'])

        self.assertIn(expected_raid_controller,
                      self.drac_client.list_raid_controllers())

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_list_virtual_disks(self, mock_requests,
                                mock_wait_until_idrac_is_ready):
        expected_virtual_disk = raid.VirtualDisk(
            id='Disk.Virtual.0:RAID.Integrated.1-1',
            name='disk 0',
            description='Virtual Disk 0 on Integrated RAID Controller 1',
            controller='RAID.Integrated.1-1',
            raid_level='1',
            size_mb=571776,
            status='ok',
            raid_status='online',
            span_depth=1,
            span_length=2,
            pending_operations=None,
            physical_disks=[
                'Disk.Bay.0:Enclosure.Internal.0-1:RAID.Integrated.1-1',
                'Disk.Bay.1:Enclosure.Internal.0-1:RAID.Integrated.1-1'
            ])

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_VirtualDiskView]['ok'])

        self.assertIn(expected_virtual_disk,
                      self.drac_client.list_virtual_disks())

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_list_physical_disks(self, mock_requests,
                                 mock_wait_until_idrac_is_ready):
        expected_physical_disk = raid.PhysicalDisk(
            id='Disk.Bay.1:Enclosure.Internal.0-1:RAID.Integrated.1-1',
            description=('Disk 1 in Backplane 1 of '
                         'Integrated RAID Controller 1'),
            controller='RAID.Integrated.1-1',
            manufacturer='SEAGATE',
            model='ST600MM0006',
            media_type='hdd',
            interface_type='sas',
            size_mb=571776,
            free_size_mb=571776,
            serial_number='S0M3EY2Z',
            firmware_version='LS0A',
            status='ok',
            raid_status='ready',
            sas_address='5000C5007764F409',
            device_protocol=None)

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_PhysicalDiskView]['ok'])

        self.assertIn(expected_physical_disk,
                      self.drac_client.list_physical_disks())

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_list_physical_disks_direct(self, mock_requests,
                                        mock_wait_until_idrac_is_ready):
        expected_physical_disk = raid.PhysicalDisk(
            id='Disk.Direct.2:RAID.Integrated.1-1',
            description=('Disk 2 on '
                         'Integrated RAID Controller 1'),
            controller='RAID.Integrated.1-1',
            manufacturer='ATA',
            model='ST600MM0007',
            media_type='ssd',
            interface_type='sata',
            size_mb=571776,
            free_size_mb=571776,
            serial_number='S0M3EY3Z',
            firmware_version='LS0B',
            status='ok',
            raid_status='ready',
            sas_address='5000C5007764F409',
            device_protocol=None)

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_PhysicalDiskView]['ok'])

        self.assertIn(expected_physical_disk,
                      self.drac_client.list_physical_disks())

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_list_physical_disks_nvme(self, mock_requests,
                                      mock_wait_until_idrac_is_ready):
        expected_physical_disk = raid.PhysicalDisk(
            id='Disk.Bay.20:Enclosure.Internal.0-1:PCIeExtender.Slot.1',
            description='PCIe SSD in Slot 20 in Bay 1',
            controller='PCIeExtender.Slot.1',
            manufacturer='SAMSUNG',
            model='Dell Express Flash PM1725a 800GB SFF',
            media_type='ssd',
            interface_type='pcie',
            size_mb=763097,
            free_size_mb=None,
            serial_number='S39YNX0JB02343',
            firmware_version='1.0.4',
            status='unknown',
            raid_status=None,
            sas_address=None,
            device_protocol='NVMe-MI1.0')

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_PhysicalDiskView]['ok'])

        self.assertIn(expected_physical_disk,
                      self.drac_client.list_physical_disks())

    # Verify that various client convert_physical_disks calls to dracclient
    # result in a WSMan.invoke with appropriate parameters
    def _random_term(self):
        return "".join(random.sample('ABCDEFGHabcdefgh0123456',
                                     random.randint(4, 12)))

    def _random_fqdd(self):
        result = self._random_term()
        for i in range(0, random.randint(6, 10)):
            result += random.sample('.:-', 1)[0] + self._random_term()
        return result

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_convert_physical_disks_1(self, mock_requests, mock_invoke):
        '''Convert a single disk to RAID mode'''
        device_fqdd = self._random_fqdd()
        expected_invocation = 'ConvertToRAID'
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'PDArray': [device_fqdd]}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.RAIDInvocations[uris.DCIM_RAIDService][
                'ConvertToRAID']['ok'])

        result = self.drac_client.convert_physical_disks(
            raid_controller='controller',
            physical_disks=[device_fqdd],
            raid_enable=True)

        self.assertEqual({'is_commit_required': True,
                          'is_reboot_required': constants.RebootRequired.true},
                         result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, expected_invocation,
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_convert_physical_disks_n(self, mock_requests, mock_invoke):
        '''Convert a number of disks to RAID mode'''
        device_list = []
        for i in range(0, random.randint(2, 10)):
            device_list += self._random_fqdd()

        expected_invocation = 'ConvertToRAID'
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'PDArray': device_list}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.RAIDInvocations[uris.DCIM_RAIDService][
                'ConvertToRAID']['ok'])

        result = self.drac_client.convert_physical_disks(
            raid_controller='controller',
            physical_disks=device_list,
            raid_enable=True)

        self.assertEqual({'is_commit_required': True,
                          'is_reboot_required': constants.RebootRequired.true},
                         result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, expected_invocation,
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_convert_physical_disks_nonraid_1(self, mock_requests,
                                              mock_invoke):
        '''Convert a single disk to non-RAID mode'''
        device_fqdd = self._random_fqdd()
        expected_invocation = 'ConvertToNonRAID'
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'PDArray': [device_fqdd]}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.RAIDInvocations[uris.DCIM_RAIDService][
                'ConvertToRAID']['ok'])

        result = self.drac_client.convert_physical_disks(
            raid_controller='controller',
            physical_disks=[device_fqdd],
            raid_enable=False)

        self.assertEqual({'is_commit_required': True,
                          'is_reboot_required': constants.RebootRequired.true},
                         result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, expected_invocation,
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_convert_physical_disks_nonraid_n(self, mock_requests,
                                              mock_invoke):
        '''Convert a number of disks to non-RAID mode'''
        device_list = []
        for i in range(0, random.randint(2, 10)):
            device_list += self._random_fqdd()

        expected_invocation = 'ConvertToNonRAID'
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'PDArray': device_list}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.RAIDInvocations[uris.DCIM_RAIDService][
                'ConvertToRAID']['ok'])

        result = self.drac_client.convert_physical_disks(
            raid_controller='controller',
            physical_disks=device_list,
            raid_enable=False)

        self.assertEqual({'is_commit_required': True,
                          'is_reboot_required': constants.RebootRequired.true},
                         result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, expected_invocation,
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_convert_physical_disks_fail(self, mock_requests,
                                         mock_wait_until_idrac_is_ready):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDInvocations[
                uris.DCIM_RAIDService]['ConvertToRAID']['error'])

        self.assertRaises(
            exceptions.DRACOperationFailed,
            self.drac_client.convert_physical_disks,
            raid_controller='controller',
            physical_disks=['Disk0:Enclosure-1:RAID-1',
                            'Disk1:Enclosure-1:RAID-1'],
            raid_enable=True)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_create_virtual_disk(self, mock_requests, mock_invoke):
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'Target': 'controller',
                               'PDArray': ['disk1', 'disk2'],
                               'VDPropNameArray': ['Size', 'RAIDLevel'],
                               'VDPropValueArray': ['42', '4']}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.RAIDInvocations[uris.DCIM_RAIDService][
                'CreateVirtualDisk']['ok'])

        result = self.drac_client.create_virtual_disk(
            raid_controller='controller', physical_disks=['disk1', 'disk2'],
            raid_level='1', size_mb=42)

        self.assertEqual({'is_commit_required': True,
                          'is_reboot_required': constants.RebootRequired.true},
                         result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, 'CreateVirtualDisk',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_create_virtual_disk_with_extra_params(self, mock_requests,
                                                   mock_invoke):
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'Target': 'controller',
                               'PDArray': ['disk1', 'disk2'],
                               'VDPropNameArray': ['Size', 'RAIDLevel',
                                                   'VirtualDiskName',
                                                   'SpanDepth', 'SpanLength'],
                               'VDPropValueArray': ['42', '4', 'name', '3',
                                                    '2']}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.RAIDInvocations[uris.DCIM_RAIDService][
                'CreateVirtualDisk']['ok'])

        result = self.drac_client.create_virtual_disk(
            raid_controller='controller', physical_disks=['disk1', 'disk2'],
            raid_level='1', size_mb=42, disk_name='name', span_length=2,
            span_depth=3)

        self.assertEqual({'is_commit_required': True,
                          'is_reboot_required': constants.RebootRequired.true},
                         result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, 'CreateVirtualDisk',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_create_virtual_disk_fail(self, mock_requests,
                                      mock_wait_until_idrac_is_ready):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDInvocations[
                uris.DCIM_RAIDService]['CreateVirtualDisk']['error'])

        self.assertRaises(
            exceptions.DRACOperationFailed,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=['disk1', 'disk2'], raid_level='1', size_mb=42,
            disk_name='name', span_length=2, span_depth=3)

    def test_create_virtual_disk_missing_controller(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller=None,
            physical_disks=['disk1', 'disk2'], raid_level='1', size_mb=42,
            disk_name='name', span_length=2, span_depth=3)

    def test_create_virtual_disk_missing_physical_disks(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=None, raid_level='1', size_mb=42,
            disk_name='name', span_length=2, span_depth=3)

    def test_create_virtual_disk_missing_raid_level(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=['disk1', 'disk2'], raid_level=None, size_mb=42,
            disk_name='name', span_length=2, span_depth=3)

    def test_create_virtual_disk_invalid_raid_level(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=['disk1', 'disk2'], raid_level='foo', size_mb=42,
            disk_name='name', span_length=2, span_depth=3)

    def test_create_virtual_disk_missing_size(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=['disk1', 'disk2'], raid_level='1', size_mb=None,
            disk_name='name', span_length=2, span_depth=3)

    # This test is specifically for support of creating a RAID1 on a Dell BOSS
    # card.  It requires that size_mb is set to 0
    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_create_virtual_disk_0_size(self, mock_requests, mock_invoke):
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.RAIDInvocations[uris.DCIM_RAIDService][
                'CreateVirtualDisk']['ok'])

        self.drac_client.create_virtual_disk(
            raid_controller='controller',
            physical_disks=['disk1', 'disk2'],
            raid_level='1',
            size_mb=0,
            disk_name='name',
            span_length=1,
            span_depth=2)

    def test_create_virtual_disk_invalid_size(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=['disk1', 'disk2'], raid_level='1',
            size_mb='foo', disk_name='name', span_length=2, span_depth=3)

    def test_create_virtual_disk_invalid_span_length(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=['disk1', 'disk2'], raid_level='1', size_mb=42,
            disk_name='name', span_length='foo', span_depth=3)

    def test_create_virtual_disk_invalid_span_depth(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=['disk1', 'disk2'], raid_level='1', size_mb=42,
            disk_name='name', span_length=2, span_depth='foo')

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_delete_virtual_disk(self, mock_requests, mock_invoke):
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'Target': 'disk1'}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.RAIDInvocations[uris.DCIM_RAIDService][
                'DeleteVirtualDisk']['ok'])

        result = self.drac_client.delete_virtual_disk('disk1')

        self.assertEqual({'is_commit_required': True,
                          'is_reboot_required': constants.RebootRequired.true},
                         result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, 'DeleteVirtualDisk',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_delete_virtual_disk_fail(self, mock_requests,
                                      mock_wait_until_idrac_is_ready):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDInvocations[
                uris.DCIM_RAIDService]['DeleteVirtualDisk']['error'])

        self.assertRaises(
            exceptions.DRACOperationFailed,
            self.drac_client.delete_virtual_disk, 'disk1')

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_commit_pending_raid_changes(self, mock_requests,
                                         mock_create_config_job):
        self.drac_client.commit_pending_raid_changes('controller',
                                                     realtime=False)

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_RAIDService,
            cim_creation_class_name='DCIM_RAIDService',
            cim_name='DCIM:RAIDService', target='controller', reboot=False,
            start_time='TIME_NOW', realtime=False)

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_commit_pending_raid_changes_with_reboot(self, mock_requests,
                                                     mock_create_config_job):
        self.drac_client.commit_pending_raid_changes('controller',
                                                     reboot=True,
                                                     realtime=False)

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_RAIDService,
            cim_creation_class_name='DCIM_RAIDService',
            cim_name='DCIM:RAIDService', target='controller', reboot=True,
            start_time='TIME_NOW', realtime=False)

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_commit_pending_raid_changes_with_start_time(
            self, mock_requests,
            mock_create_config_job):
        timestamp = '20140924140201'
        self.drac_client.commit_pending_raid_changes('controller',
                                                     start_time=timestamp,
                                                     realtime=False)

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_RAIDService,
            cim_creation_class_name='DCIM_RAIDService',
            cim_name='DCIM:RAIDService', target='controller', reboot=False,
            start_time=timestamp, realtime=False)

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_commit_pending_raid_changes_with_reboot_and_start_time(
            self, mock_requests,
            mock_create_config_job):
        timestamp = '20140924140201'
        self.drac_client.commit_pending_raid_changes('controller',
                                                     reboot=True,
                                                     start_time=timestamp,
                                                     realtime=False)

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_RAIDService,
            cim_creation_class_name='DCIM_RAIDService',
            cim_name='DCIM:RAIDService', target='controller', reboot=True,
            start_time=timestamp, realtime=False)

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_commit_pending_raid_changes_with_realtime(
            self, mock_requests,
            mock_create_config_job):
        timestamp = '20140924140201'
        self.drac_client.commit_pending_raid_changes('controller',
                                                     reboot=False,
                                                     start_time=timestamp,
                                                     realtime=True)

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_RAIDService,
            cim_creation_class_name='DCIM_RAIDService',
            cim_name='DCIM:RAIDService', target='controller', reboot=False,
            start_time=timestamp, realtime=True)

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'delete_pending_config', spec_set=True, autospec=True)
    def test_abandon_pending_raid_changes(self, mock_requests,
                                          mock_delete_pending_config):
        self.drac_client.abandon_pending_raid_changes('controller')

        mock_delete_pending_config.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_RAIDService,
            cim_creation_class_name='DCIM_RAIDService',
            cim_name='DCIM:RAIDService', target='controller')

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'delete_pending_config', spec_set=True, autospec=True)
    def test_abandon_pending_raid_changes_realtime(self, mock_requests,
                                                   mock_delete_pending_config):
        self.drac_client.abandon_pending_raid_changes('controller')

        mock_delete_pending_config.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_RAIDService,
            cim_creation_class_name='DCIM_RAIDService',
            cim_name='DCIM:RAIDService', target='controller')

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'convert_physical_disks',
                       return_value={}, spec_set=True,
                       autospec=True)
    def test_raid_controller_jbod_capable(self, mock_requests,
                                          mock_wait_until_idrac_is_ready,
                                          mock_convert_physical_disks):

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_PhysicalDiskView]['ok'])

        is_jbod = self.drac_client.is_jbod_capable(self.raid_controller_fqdd)

        self.assertTrue(is_jbod, msg="is_jbod is true")

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'convert_physical_disks',
                       return_value={}, spec_set=True,
                       autospec=True)
    def test_raid_controller_jbod_non_raid(self, mock_requests,
                                           mock_wait_until_idrac_is_ready,
                                           mock_convert_physical_disks):

        pdv = test_utils.RAIDEnumerations[uris.DCIM_PhysicalDiskView]['ok']
        # change to non-RAID value
        pdv = pdv.replace("<n1:RaidStatus>1</n1:RaidStatus>",
                          "<n1:RaidStatus>8</n1:RaidStatus>")

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=pdv)

        is_jbod = self.drac_client.is_jbod_capable(self.raid_controller_fqdd)

        self.assertTrue(is_jbod, msg="is_jbod is true")

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'convert_physical_disks',
                       return_value={}, spec_set=True,
                       autospec=True)
    def test_raid_controller_jbod_unknown(self, mock_requests,
                                          mock_wait_until_idrac_is_ready,
                                          mock_convert_physical_disks):

        is_jbod = False
        pdv = test_utils.RAIDEnumerations[uris.DCIM_PhysicalDiskView]['ok']
        # change to non-RAID value
        pdv = pdv.replace("<n1:RaidStatus>1</n1:RaidStatus>",
                          "<n1:RaidStatus>0</n1:RaidStatus>")

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=pdv)
        self.assertRaises(exceptions.DRACRequestFailed,
                          self.drac_client.is_jbod_capable,
                          self.raid_controller_fqdd)
        self.assertFalse(is_jbod, msg="is_jbod is false")

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'convert_physical_disks',
                       spec_set=True,
                       autospec=True)
    def test_raid_controller_jbod_not_supported(self,
                                                mock_requests,
                                                mock_convert_physical_disks,
                                                mock_wait_idrac_is_ready):

        msg = " operation is not supported on th"
        exc = exceptions.DRACOperationFailed(drac_messages=msg)
        mock_convert_physical_disks.side_effect = exc

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_PhysicalDiskView]['ok'])

        is_jbod = self.drac_client.is_jbod_capable(self.raid_controller_fqdd)
        self.assertFalse(is_jbod, msg="is_jbod is false")

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'convert_physical_disks',
                       spec_set=True,
                       autospec=True)
    def test_raid_controller_jbod_ex_no_match(self,
                                              mock_requests,
                                              mock_convert_physical_disks,
                                              mock_wait_until_idrac_is_ready):

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_PhysicalDiskView]['ok'])
        msg = "NON_MATCHING_MESSAGE"
        exc = exceptions.DRACOperationFailed(drac_messages=msg)
        mock_convert_physical_disks.side_effect = exc

        self.assertRaises(
            exceptions.DRACOperationFailed,
            self.drac_client.is_jbod_capable, self.raid_controller_fqdd)

    def test_is_raid_controller(self, mock_requests):
        self.assertTrue(self.drac_client
                        .is_raid_controller("RAID.Integrated.1-1"))
        self.assertFalse(self.drac_client
                         .is_raid_controller("notRAID.Integrated.1-1"))

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_is_boss_controller(self, mock_requests,
                                mock_wait_until_idrac_is_ready):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_ControllerView]['ok'])
        self.assertTrue(self.drac_client
                        .is_boss_controller("AHCI.Integrated.1-1"))

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_is_not_boss_controller(self, mock_requests,
                                    mock_wait_until_idrac_is_ready):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_ControllerView]['ok'])
        self.assertFalse(self.drac_client
                         .is_boss_controller("notAHCI.Integrated.1-1"),
                         None)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_is_boss_controller_with_cntl_list(self, mock_requests,
                                               mock_wait_until_idrac_is_ready):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_ControllerView]['ok'])
        controllers = self.drac_client.list_raid_controllers()
        self.assertTrue(self.drac_client
                        .is_boss_controller("AHCI.Integrated.1-1",
                                            controllers))

    def test_check_disks_status_no_controllers(self, mock_requests):
        physical_disks = [self.disk_1, self.disk_2, self.disk_3, self.disk_4]
        raid_mgt = self.drac_client._raid_mgmt

        cont_to_phys_disk_ids = collections.defaultdict(list)
        mode = constants.RaidStatus.jbod

        raid_mgt._check_disks_status(mode, physical_disks,
                                     cont_to_phys_disk_ids)
        jbod_len = len(cont_to_phys_disk_ids['RAID.Integrated.1-1'])
        self.assertEqual(jbod_len, 0)

        # Switch mode to RAID and try again
        cont_to_phys_disk_ids = collections.defaultdict(list)
        mode = constants.RaidStatus.raid
        raid_mgt._check_disks_status(mode, physical_disks,
                                     cont_to_phys_disk_ids)
        raid_len = len(cont_to_phys_disk_ids['RAID.Integrated.1-1'])
        self.assertEqual(raid_len, 0)

    def test_check_disks_status_bad(self, mock_requests):
        mode = constants.RaidStatus.raid
        disk_2 = self.disk_2._replace(raid_status='FAKE_STATUS')
        physical_disks = [self.disk_1, disk_2, self.disk_3, self.disk_4]
        raid_mgt = self.drac_client._raid_mgmt

        self.assertRaises(ValueError,
                          raid_mgt._check_disks_status,
                          mode,
                          physical_disks,
                          self.controllers_to_physical_disk_ids.copy())
        mode = constants.RaidStatus.jbod
        self.assertRaises(ValueError,
                          raid_mgt._check_disks_status,
                          mode,
                          physical_disks,
                          self.controllers_to_physical_disk_ids.copy())

    def test_check_disks_status_fail(self, mock_requests):
        mode = constants.RaidStatus.raid
        disk_2_failed = self.disk_2._replace(raid_status='failed')
        physical_disks = [self.disk_1, disk_2_failed, self.disk_3, self.disk_4]
        raid_mgt = self.drac_client._raid_mgmt

        self.assertRaises(ValueError,
                          raid_mgt._check_disks_status,
                          mode,
                          physical_disks,
                          self.controllers_to_physical_disk_ids.copy())
        mode = constants.RaidStatus.jbod
        self.assertRaises(ValueError,
                          raid_mgt._check_disks_status,
                          mode,
                          physical_disks,
                          self.controllers_to_physical_disk_ids.copy())

    def test_check_disks_status_no_change(self, mock_requests):
        raid_mgt = self.drac_client._raid_mgmt
        mode = constants.RaidStatus.raid
        physical_disks = [self.disk_1, self.disk_2,
                          self.disk_3, self.disk_4]

        raid_cntl_to_phys_disk_ids = (self.controllers_to_physical_disk_ids.
                                      copy())

        raid_mgt._check_disks_status(mode,  physical_disks,
                                     raid_cntl_to_phys_disk_ids)
        raid_len = len(raid_cntl_to_phys_disk_ids['RAID.Integrated.1-1'])
        self.assertEqual(raid_len, 0)

        mode = constants.RaidStatus.jbod
        disk_1_non_raid = self.disk_1._replace(raid_status='non-RAID')
        disk_2_non_raid = self.disk_2._replace(raid_status='non-RAID')
        physical_disks = [disk_1_non_raid, disk_2_non_raid,
                          self.disk_3, self.disk_4]

        jbod_cntl_to_phys_disk_ids = (self.controllers_to_physical_disk_ids.
                                      copy())
        raid_mgt._check_disks_status(mode,  physical_disks,
                                     jbod_cntl_to_phys_disk_ids)
        jbod_len = len(jbod_cntl_to_phys_disk_ids['RAID.Integrated.1-1'])
        self.assertEqual(jbod_len, 0)

    def test_check_disks_status_change_state(self, mock_requests):
        raid_mgt = self.drac_client._raid_mgmt
        mode = constants.RaidStatus.jbod
        physical_disks = [self.disk_1, self.disk_2, self.disk_3, self.disk_4]

        jbod_cntl_to_phys_disk_ids = (self.controllers_to_physical_disk_ids.
                                      copy())

        raid_mgt._check_disks_status(mode, physical_disks,
                                     jbod_cntl_to_phys_disk_ids)
        jbod_len = len(jbod_cntl_to_phys_disk_ids['RAID.Integrated.1-1'])
        self.assertEqual(jbod_len, 2)

        mode = constants.RaidStatus.raid
        disk_1_non_raid = self.disk_1._replace(raid_status='non-RAID')
        disk_2_non_raid = self.disk_2._replace(raid_status='non-RAID')
        physical_disks = [disk_1_non_raid, disk_2_non_raid,
                          self.disk_3, self.disk_4]
        raid_cntl_to_phys_disk_ids = (self.controllers_to_physical_disk_ids.
                                      copy())
        raid_mgt._check_disks_status(mode,  physical_disks,
                                     raid_cntl_to_phys_disk_ids)
        raid_len = len(raid_cntl_to_phys_disk_ids['RAID.Integrated.1-1'])
        self.assertEqual(raid_len, 2)

    def test_check_disks_status_bad_and_fail(self, mock_requests):
        mode = constants.RaidStatus.raid
        disk_1_bad = self.disk_1._replace(raid_status='FAKE_STATUS')
        disk_2_failed = self.disk_2._replace(raid_status='failed')
        physical_disks = [disk_1_bad, disk_2_failed, self.disk_3, self.disk_4]
        raid_mgt = self.drac_client._raid_mgmt

        self.assertRaises(ValueError,
                          raid_mgt._check_disks_status,
                          mode,
                          physical_disks,
                          self.controllers_to_physical_disk_ids.copy())
        mode = constants.RaidStatus.jbod
        self.assertRaises(ValueError,
                          raid_mgt._check_disks_status,
                          mode,
                          physical_disks,
                          self.controllers_to_physical_disk_ids.copy())

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'convert_physical_disks', spec_set=True,
                       autospec=True)
    def test_change_physical_disk_state_jbod(
            self, mock_requests,
            mock_convert_physical_disks,
            wait_until_idrac_is_ready):
        mode = constants.RaidStatus.jbod
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_PhysicalDiskView]['ok'])
        mock_convert_physical_disks.return_value = {'is_commit_required': True,
                                                    'is_reboot_required':
                                                    constants.RebootRequired
                                                    .true}
        cntl_to_phys_d_ids = self.controllers_to_physical_disk_ids
        results = self.drac_client.change_physical_disk_state(
            mode, cntl_to_phys_d_ids)
        self.assertTrue(results["is_reboot_required"])
        self.assertEqual(len(results["commit_required_ids"]), 2)

    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'list_physical_disks', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'convert_physical_disks', spec_set=True,
                       autospec=True)
    def test_change_physical_disk_state_raid(
            self, mock_requests,
            mock_convert_physical_disks,
            mock_list_physical_disks):
        mode = constants.RaidStatus.raid
        disk_1_non_raid = self.disk_1._replace(raid_status='non-RAID')
        disk_2_non_raid = self.disk_2._replace(raid_status='non-RAID')
        physical_disks = [disk_1_non_raid, disk_2_non_raid,
                          self.disk_3, self.disk_4]
        mock_list_physical_disks.return_value = physical_disks
        mock_convert_physical_disks.return_value = {'is_commit_required': True,
                                                    'is_reboot_required':
                                                    constants.RebootRequired
                                                    .true}
        cntl_to_phys_d_ids = self.controllers_to_physical_disk_ids
        results = self.drac_client.change_physical_disk_state(
            mode, cntl_to_phys_d_ids)
        self.assertTrue(results["is_reboot_required"])
        self.assertEqual(len(results["commit_required_ids"]), 1)

    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'list_physical_disks', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'convert_physical_disks', spec_set=True,
                       autospec=True)
    def test_change_physical_disk_state_none(
            self, mock_requests,
            mock_convert_physical_disks,
            mock_list_physical_disks):
        mode = constants.RaidStatus.raid
        physical_disks = [self.disk_1, self.disk_2, self.disk_3, self.disk_4]
        mock_convert_physical_disks.return_value = {'is_commit_required': True,
                                                    'is_reboot_required':
                                                    constants.RebootRequired
                                                    .true}
        mock_list_physical_disks.return_value = physical_disks
        cntl_to_phys_d_ids = self.controllers_to_physical_disk_ids
        results = self.drac_client.change_physical_disk_state(
            mode, cntl_to_phys_d_ids)
        self.assertFalse(results["is_reboot_required"])
        self.assertEqual(len(results["commit_required_ids"]), 0)

    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'list_physical_disks', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'convert_physical_disks', spec_set=True,
                       autospec=True,
                       side_effect=exceptions.DRACOperationFailed(
                           drac_messages=constants.NOT_SUPPORTED_MSG))
    def test_change_physical_disk_state_not_supported(
            self, mock_requests,
            mock_convert_physical_disks,
            mock_list_physical_disks):
        mode = constants.RaidStatus.raid
        disk_1_non_raid = self.disk_1._replace(raid_status='non-RAID')
        disk_2_non_raid = self.disk_2._replace(raid_status='non-RAID')
        physical_disks = [disk_1_non_raid, disk_2_non_raid,
                          self.disk_3, self.disk_4]
        mock_list_physical_disks.return_value = physical_disks
        cntl_to_phys_d_ids = self.controllers_to_physical_disk_ids
        results = self.drac_client.change_physical_disk_state(
            mode, cntl_to_phys_d_ids)
        self.assertFalse(results["is_reboot_required"])
        self.assertEqual(len(results["commit_required_ids"]), 0)

    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'list_physical_disks', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'convert_physical_disks', spec_set=True,
                       autospec=True,
                       side_effect=exceptions.DRACOperationFailed(
                           drac_messages="OTHER_MESSAGE"))
    def test_change_physical_disk_state_raise_drac_operation_other(
            self, mock_requests,
            mock_convert_physical_disks,
            mock_list_physical_disks):
        mode = constants.RaidStatus.raid
        disk_1_non_raid = self.disk_1._replace(raid_status='non-RAID')
        disk_2_non_raid = self.disk_2._replace(raid_status='non-RAID')
        physical_disks = [disk_1_non_raid, disk_2_non_raid,
                          self.disk_3, self.disk_4]
        mock_list_physical_disks.return_value = physical_disks
        cntl_to_phys_d_ids = self.controllers_to_physical_disk_ids
        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed,
            "OTHER_MESSAGE",
            self.drac_client.change_physical_disk_state,
            mode, cntl_to_phys_d_ids)

    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'list_physical_disks', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'convert_physical_disks', spec_set=True,
                       autospec=True, side_effect=Exception(
                           "SOMETHING_BAD_HAPPENED"))
    def test_change_physical_disk_state_raise_other(
            self, mock_requests,
            mock_convert_physical_disks,
            mock_list_physical_disks):
        mode = constants.RaidStatus.raid
        disk_1_non_raid = self.disk_1._replace(raid_status='non-RAID')
        disk_2_non_raid = self.disk_2._replace(raid_status='non-RAID')
        physical_disks = [disk_1_non_raid, disk_2_non_raid,
                          self.disk_3, self.disk_4]
        mock_list_physical_disks.return_value = physical_disks
        cntl_to_phys_d_ids = self.controllers_to_physical_disk_ids
        self.assertRaisesRegexp(
            Exception, "SOMETHING_BAD_HAPPENED",
            self.drac_client.change_physical_disk_state,
            mode, cntl_to_phys_d_ids)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'list_physical_disks', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'convert_physical_disks', spec_set=True,
                       autospec=True)
    def test_change_physical_disk_state_with_no_dict(
            self, mock_requests,
            mock_convert_physical_disks,
            mock_list_physical_disks,
            mock_wait_until_idrac_is_ready):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_ControllerView]['ok'])
        mode = constants.RaidStatus.jbod
        physical_disks = [self.disk_1, self.disk_2, self.disk_3, self.disk_4]
        mock_convert_physical_disks.return_value = {'is_commit_required': True,
                                                    'is_reboot_required':
                                                    constants.RebootRequired
                                                    .true}
        mock_list_physical_disks.return_value = physical_disks
        results = self.drac_client.change_physical_disk_state(mode)
        self.assertTrue(results["is_reboot_required"])
        self.assertEqual(len(results["commit_required_ids"]), 2)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'list_physical_disks', spec_set=True,
                       autospec=True)
    def test_change_physical_disk_state_with_no_raid_or_boss_card_match(
            self, mock_requests,
            mock_list_physical_disks,
            mock_wait_until_idrac_is_ready):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_ControllerView]['ok'])
        mode = constants.RaidStatus.jbod
        _disk_1 = self.disk_1._replace(controller='NOT_RAID.Integrated.1-1')
        _disk_2 = self.disk_2._replace(controller='NOT_RAID.Integrated.1-1')
        _disk_3 = self.disk_3._replace(controller='NOT_AHCI.Integrated.1-1')
        _disk_4 = self.disk_4._replace(controller='NOT_AHCI.Integrated.1-1')
        physical_disks = [_disk_1, _disk_2, _disk_3, _disk_4]
        mock_list_physical_disks.return_value = physical_disks
        results = self.drac_client.change_physical_disk_state(mode)
        self.assertFalse(results["is_reboot_required"])
        self.assertEqual(len(results["commit_required_ids"]), 0)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'list_physical_disks', spec_set=True,
                       autospec=True)
    @mock.patch.object(dracclient.resources.raid.RAIDManagement,
                       'convert_physical_disks', spec_set=True,
                       autospec=True)
    def test_change_physical_disk_state_conversion_return_values(
            self, mock_requests,
            mock_convert_physical_disks,
            mock_list_physical_disks,
            mock_wait_until_idrac_is_ready):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_ControllerView]['ok'])
        mode = constants.RaidStatus.jbod
        physical_disks = [self.disk_1, self.disk_2, self.disk_3, self.disk_4]
        '''Test all logic branches for 100% coverage, it is unlikely
        convert_physical_disks() will return empty dict but we do check
        for this case in change_physical_disk_state()'''
        mock_convert_physical_disks.return_value = {}
        mock_list_physical_disks.return_value = physical_disks
        results = self.drac_client.change_physical_disk_state(mode)
        self.assertFalse(results["is_reboot_required"])
        self.assertEqual(len(results["commit_required_ids"]), 0)
        '''Where convert_physical_disks() does not require a commit after
        executing, unlikely case but provides 100% code coverage of all
        logic branches.'''
        mock_convert_physical_disks.return_value = {'is_commit_required':
                                                    False,
                                                    'is_reboot_required':
                                                    constants.RebootRequired
                                                    .false}
        results = self.drac_client.change_physical_disk_state(mode)
        self.assertFalse(results["is_reboot_required"])
        self.assertEqual(len(results["commit_required_ids"]), 0)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_is_realtime_supported_with_realtime_controller(
            self,
            mock_requests,
            mock_wait_until_idrac_is_ready):
        expected_raid_controller = 'RAID.Integrated.1-1'

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_ControllerView]['ok'])

        self.assertTrue(
                self.drac_client.is_realtime_supported(
                    expected_raid_controller))

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_is_realtime_supported_with_non_realtime_controller(
            self,
            mock_requests,
            mock_wait_until_idrac_is_ready):
        expected_raid_controller = 'AHCI.Integrated.1-1'

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_ControllerView]['ok'])

        self.assertFalse(
                self.drac_client.is_realtime_supported(
                    expected_raid_controller))
