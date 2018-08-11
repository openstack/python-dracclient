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

import datetime
import lxml.etree
import mock
import re
import requests_mock

import dracclient.client
from dracclient import constants
from dracclient import exceptions
from dracclient.resources.inventory import NIC
import dracclient.resources.job
from dracclient.resources import nic
from dracclient.resources import uris
from dracclient.tests import base
from dracclient.tests import utils as test_utils


@requests_mock.Mocker()
@mock.patch.object(dracclient.client.WSManClient, 'wait_until_idrac_is_ready',
                   spec_set=True, autospec=True)
class ClientNICTestCase(base.BaseTest):

    def setUp(self):
        super(ClientNICTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    def test_list_nics(self, mock_requests,
                       mock_wait_until_idrac_is_ready):
        expected_nics = [
            NIC(id='NIC.Embedded.1-1-1',
                mac='B0:83:FE:C6:6F:A1',
                model='Broadcom Gigabit Ethernet BCM5720 - B0:83:FE:C6:6F:A1',
                speed_mbps=1000,
                duplex='full duplex',
                media_type='Base T'),
            NIC(id='NIC.Slot.2-1-1',
                mac='A0:36:9F:52:7D:1E',
                model='Intel(R) Gigabit 2P I350-t Adapter - A0:36:9F:52:7D:1E',
                speed_mbps=1000,
                duplex='full duplex',
                media_type='Base T'),
            NIC(id='NIC.Slot.2-2-1',
                mac='A0:36:9F:52:7D:1F',
                model='Intel(R) Gigabit 2P I350-t Adapter - A0:36:9F:52:7D:1F',
                speed_mbps=1000,
                duplex='full duplex',
                media_type='Base T'),
            NIC(id='NIC.Embedded.2-1-1',
                mac='B0:83:FE:C6:6F:A2',
                model='Broadcom Gigabit Ethernet BCM5720 - B0:83:FE:C6:6F:A2',
                speed_mbps=1000,
                duplex='full duplex',
                media_type='Base T')
        ]

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.InventoryEnumerations[uris.DCIM_NICView]['ok'])

        self.assertEqual(expected_nics, self.drac_client.list_nics())

    def test_list_nics_sorted(self, mock_requests,
                              mock_wait_until_idrac_is_ready):
        expected_nics = [
            NIC(id='NIC.Embedded.1-1-1',
                mac='B0:83:FE:C6:6F:A1',
                model='Broadcom Gigabit Ethernet BCM5720 - B0:83:FE:C6:6F:A1',
                speed_mbps=1000,
                duplex='full duplex',
                media_type='Base T'),
            NIC(id='NIC.Embedded.2-1-1',
                mac='B0:83:FE:C6:6F:A2',
                model='Broadcom Gigabit Ethernet BCM5720 - B0:83:FE:C6:6F:A2',
                speed_mbps=1000,
                duplex='full duplex',
                media_type='Base T'),
            NIC(id='NIC.Slot.2-1-1',
                mac='A0:36:9F:52:7D:1E',
                model='Intel(R) Gigabit 2P I350-t Adapter - A0:36:9F:52:7D:1E',
                speed_mbps=1000,
                duplex='full duplex',
                media_type='Base T'),
            NIC(id='NIC.Slot.2-2-1',
                mac='A0:36:9F:52:7D:1F',
                model='Intel(R) Gigabit 2P I350-t Adapter - A0:36:9F:52:7D:1F',
                speed_mbps=1000,
                duplex='full duplex',
                media_type='Base T')
        ]

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.InventoryEnumerations[uris.DCIM_NICView]['ok'])

        self.assertEqual(expected_nics, self.drac_client.list_nics(sort=True))

    def test_list_nic_settings(self, mock_requests,
                               mock_wait_until_idrac_is_ready):
        expected_enum_attr = nic.NICEnumerationAttribute(
            name='BootStrapType',
            instance_id='NIC.Integrated.1-3-1:BootStrapType',
            fqdd='NIC.Integrated.1-3-1',
            read_only=False,
            current_value='AutoDetect',
            pending_value=None,
            possible_values=['AutoDetect', 'BBS', 'Int18h', 'Int19h'])

        expected_string_attr = nic.NICStringAttribute(
            name='BusDeviceFunction',
            instance_id='NIC.Integrated.1-3-1:BusDeviceFunction',
            fqdd='NIC.Integrated.1-3-1',
            read_only=True,
            current_value='02:00:00',
            pending_value=None,
            min_length=0,
            max_length=0,
            pcre_regex=None)

        expected_integer_attr = nic.NICIntegerAttribute(
            name='BlnkLeds',
            instance_id='NIC.Integrated.1-3-1:BlnkLeds',
            fqdd='NIC.Integrated.1-3-1',
            read_only=False,
            current_value=0,
            pending_value=None,
            lower_bound=0,
            upper_bound=15)

        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICEnumeration]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICString]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICInteger]['ok']}])

        nic_settings = self.drac_client.list_nic_settings(
            nic_id='NIC.Integrated.1-3-1')

        self.assertEqual(63, len(nic_settings))

        self.assertIn('BootStrapType', nic_settings)
        self.assertEqual(expected_enum_attr,
                         nic_settings['BootStrapType'])

        self.assertIn('BusDeviceFunction', nic_settings)
        self.assertEqual(expected_string_attr,
                         nic_settings['BusDeviceFunction'])

        self.assertIn('BlnkLeds', nic_settings)
        self.assertEqual(expected_integer_attr,
                         nic_settings['BlnkLeds'])

    def test_list_nic_settings_with_colliding_attrs(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICEnumeration]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICString]['colliding']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICInteger]['ok']}])

        self.assertRaises(
            exceptions.DRACOperationFailed,
            self.drac_client.list_nic_settings,
            nic_id='NIC.Integrated.1-3-1')

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_set_nic_settings(self, mock_requests, mock_invoke,
                              mock_wait_until_idrac_is_ready):
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICEnumeration]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICString]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICInteger]['ok']}])

        expected_selectors = {'CreationClassName': 'DCIM_NICService',
                              'Name': 'DCIM:NICService',
                              'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Target': 'NIC.Integrated.1-3-1',
                               'AttributeValue': ['PXE'],
                               'AttributeName': ['LegacyBootProto']}

        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.NICInvocations[uris.DCIM_NICService][
                'SetAttributes']['ok'])

        result = self.drac_client.set_nic_settings(
            nic_id='NIC.Integrated.1-3-1',
            settings={'LegacyBootProto': 'PXE'})

        self.assertEqual({'is_commit_required': True,
                          'is_reboot_required': constants.RebootRequired.true},
                         result)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_NICService, 'SetAttributes',
            expected_selectors, expected_properties)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_set_nic_settings_string(self, mock_requests, mock_invoke,
                                     mock_wait_until_idrac_is_ready):
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICEnumeration]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICString]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICInteger]['ok']}])

        expected_selectors = {'CreationClassName': 'DCIM_NICService',
                              'Name': 'DCIM:NICService',
                              'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Target': 'NIC.Integrated.1-3-1',
                               'AttributeValue': ['D4:AE:52:A5:B1:01'],
                               'AttributeName': ['VirtMacAddr']}

        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.NICInvocations[uris.DCIM_NICService][
                'SetAttributes']['ok'])

        result = self.drac_client.set_nic_settings(
            nic_id='NIC.Integrated.1-3-1',
            settings={'VirtMacAddr': 'D4:AE:52:A5:B1:01'})

        self.assertEqual({'is_commit_required': True,
                          'is_reboot_required': constants.RebootRequired.true},
                         result)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_NICService, 'SetAttributes',
            expected_selectors, expected_properties)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_set_nic_settings_integer(self, mock_requests, mock_invoke,
                                      mock_wait_until_idrac_is_ready):
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICEnumeration]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICString]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICInteger]['ok']}])

        expected_selectors = {'CreationClassName': 'DCIM_NICService',
                              'Name': 'DCIM:NICService',
                              'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Target': 'NIC.Integrated.1-3-1',
                               'AttributeValue': [1],
                               'AttributeName': ['SecondTgtBootLun']}

        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.NICInvocations[uris.DCIM_NICService][
                'SetAttributes']['ok'])

        result = self.drac_client.set_nic_settings(
            nic_id='NIC.Integrated.1-3-1',
            settings={'SecondTgtBootLun': 1})

        self.assertEqual({'is_commit_required': True,
                          'is_reboot_required': constants.RebootRequired.true},
                         result)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_NICService, 'SetAttributes',
            expected_selectors, expected_properties)

    def test_set_nic_settings_error(self, mock_requests,
                                    mock_wait_until_idrac_is_ready):
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICEnumeration]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICString]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICInteger]['ok']},
            {'text': test_utils.NICInvocations[
                uris.DCIM_NICService]['SetAttributes']['error']}])

        self.assertRaises(exceptions.DRACOperationFailed,
                          self.drac_client.set_nic_settings,
                          'NIC.InvalidTarget',
                          {'LegacyBootProto': 'PXE'})

    def test_set_nic_settings_with_unknown_attr(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICEnumeration]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICString]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICInteger]['ok']}])

        self.assertRaises(exceptions.InvalidParameterValue,
                          self.drac_client.set_nic_settings,
                          'NIC.Integrated.1-3-1',
                          {'foo': 'bar'})

    def test_set_nic_settings_with_unchanged_attr(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICEnumeration]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICString]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICInteger]['ok']}])

        result = self.drac_client.set_nic_settings(
            nic_id='NIC.Integrated.1-3-1',
            settings={'LegacyBootProto': 'NONE'})

        self.assertEqual({'is_commit_required': False,
                          'is_reboot_required':
                          constants.RebootRequired.false},
                         result)

    def test_set_nic_settings_with_readonly_attr(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        expected_message = (
            "Cannot set read-only iDRAC Card attributes: ['LinkStatus'].")
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICEnumeration]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICString]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICInteger]['ok']}])

        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.set_nic_settings,
            'NIC.Integrated.1-3-1',
            {'LinkStatus': 'Connected'})

    def test_set_nic_settings_with_incorrect_enum(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        expected_message = (
            "Attribute 'LegacyBootProto' cannot be set to value 'foo'. "
            "It must be in ['PXE', 'iSCSI', 'NONE'].")
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICEnumeration]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICString]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICInteger]['ok']}])

        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.set_nic_settings,
            'NIC.Integrated.1-3-1',
            {'LegacyBootProto': 'foo'})

    def test_set_nic_settings_with_incorrect_regexp(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        expected_message = (
            "Attribute 'VirtMacAddr' cannot be set to value 'foo.' "
            "It must match regex '^([0-9a-fA-F]{2}:){5}([0-9a-fA-F]{2})$'.")
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICEnumeration]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICString]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICInteger]['ok']}])

        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.set_nic_settings,
            'NIC.Integrated.1-3-1',
            {'VirtMacAddr': 'foo'})

    def test_set_nic_settings_with_out_of_bounds_value(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        expected_message = (
            "Attribute BannerMessageTimeout cannot be set to value 100. "
            "It must be between 0 and 14.")
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICEnumeration]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICString]['ok']},
            {'text': test_utils.NICEnumerations[
                uris.DCIM_NICInteger]['ok']}])

        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.set_nic_settings,
            'NIC.Integrated.1-3-1',
            {'BannerMessageTimeout': 100})


class ClientNICSettingTestCase(base.BaseTest):

    def setUp(self):
        super(ClientNICSettingTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_create_nic_config_job(self, mock_create_config_job):

        nic_id = 'NIC.Embedded.1-1-1'
        self.drac_client.create_nic_config_job(
            nic_id=nic_id)

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_NICService,
            cim_creation_class_name='DCIM_NICService',
            cim_name='DCIM:NICService',
            target=nic_id,
            reboot=False,
            start_time='TIME_NOW')

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_create_nic_config_job_reboot(self, mock_create_config_job):

        nic_id = 'NIC.Embedded.1-1-1'
        self.drac_client.create_nic_config_job(
            nic_id=nic_id,
            reboot=True)

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_NICService,
            cim_creation_class_name='DCIM_NICService',
            cim_name='DCIM:NICService',
            target=nic_id,
            reboot=True,
            start_time='TIME_NOW')

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_create_nic_config_job_time(self, mock_create_config_job):

        nic_id = 'NIC.Embedded.1-1-1'
        timestamp = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        self.drac_client.create_nic_config_job(
            nic_id=nic_id,
            start_time=timestamp)

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_NICService,
            cim_creation_class_name='DCIM_NICService',
            cim_name='DCIM:NICService',
            target=nic_id,
            reboot=False,
            start_time=timestamp)

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_create_nic_config_job_no_time(self, mock_create_config_job):

        nic_id = 'NIC.Embedded.1-1-1'
        self.drac_client.create_nic_config_job(
            nic_id=nic_id,
            start_time=None)

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_NICService,
            cim_creation_class_name='DCIM_NICService',
            cim_name='DCIM:NICService',
            target=nic_id,
            reboot=False,
            start_time=None)
