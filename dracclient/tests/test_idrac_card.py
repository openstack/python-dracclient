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

import lxml.etree
import mock
import re
import requests_mock

import dracclient.client
from dracclient import constants
from dracclient import exceptions
from dracclient.resources import idrac_card
from dracclient.resources import job
from dracclient.resources import uris
from dracclient.tests import base
from dracclient.tests import utils as test_utils


@requests_mock.Mocker()
@mock.patch.object(dracclient.client.WSManClient,
                   'wait_until_idrac_is_ready', spec_set=True,
                   autospec=True)
class ClientiDRACCardConfigurationTestCase(base.BaseTest):

    def setUp(self):
        super(ClientiDRACCardConfigurationTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    def test_list_idrac_settings_by_instance_id(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        expected_enum_attr = idrac_card.iDRACCardEnumerableAttribute(
            name='Type',
            instance_id='iDRAC.Embedded.1#Info.1#Type',
            read_only=True,
            current_value='13G Monolithic',
            pending_value=None,
            fqdd='iDRAC.Embedded.1',
            group_id='Info.1',
            possible_values=['12G/13G', '12G Monolithic', '12G Modular',
                             '13G Monolithic', '13G Modular', '12G DCS',
                             '13G DCS'])
        expected_string_attr = idrac_card.iDRACCardStringAttribute(
            name='Version',
            instance_id='iDRAC.Embedded.1#Info.1#Version',
            read_only=True,
            current_value='2.40.40.40',
            pending_value=None,
            fqdd='iDRAC.Embedded.1',
            group_id='Info.1',
            min_length=0,
            max_length=63)
        expected_integer_attr = idrac_card.iDRACCardIntegerAttribute(
            name='Port',
            instance_id='iDRAC.Embedded.1#SSH.1#Port',
            read_only=False,
            current_value=22,
            pending_value=None,
            fqdd='iDRAC.Embedded.1',
            group_id='SSH.1',
            lower_bound=1,
            upper_bound=65535)
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardEnumeration]['ok']},
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardString]['ok']},
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardInteger]['ok']}])

        idrac_settings = self.drac_client.list_idrac_settings()

        self.assertEqual(631, len(idrac_settings))
        # enumerable attribute
        self.assertIn('iDRAC.Embedded.1#Info.1#Type', idrac_settings)
        self.assertEqual(expected_enum_attr, idrac_settings[
                         'iDRAC.Embedded.1#Info.1#Type'])
        # string attribute
        self.assertIn('iDRAC.Embedded.1#Info.1#Version', idrac_settings)
        self.assertEqual(expected_string_attr,
                         idrac_settings['iDRAC.Embedded.1#Info.1#Version'])
        # integer attribute
        self.assertIn('iDRAC.Embedded.1#SSH.1#Port', idrac_settings)
        self.assertEqual(expected_integer_attr, idrac_settings[
                         'iDRAC.Embedded.1#SSH.1#Port'])

    def test_list_idrac_settings_by_name(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        expected_enum_attr = idrac_card.iDRACCardEnumerableAttribute(
            name='Type',
            instance_id='iDRAC.Embedded.1#Info.1#Type',
            read_only=True,
            current_value='13G Monolithic',
            pending_value=None,
            fqdd='iDRAC.Embedded.1',
            group_id='Info.1',
            possible_values=['12G/13G', '12G Monolithic', '12G Modular',
                             '13G Monolithic', '13G Modular', '12G DCS',
                             '13G DCS'])
        expected_string_attr = idrac_card.iDRACCardStringAttribute(
            name='Version',
            instance_id='iDRAC.Embedded.1#Info.1#Version',
            read_only=True,
            current_value='2.40.40.40',
            pending_value=None,
            fqdd='iDRAC.Embedded.1',
            group_id='Info.1',
            min_length=0,
            max_length=63)
        expected_integer_attr = idrac_card.iDRACCardIntegerAttribute(
            name='Port',
            instance_id='iDRAC.Embedded.1#SSH.1#Port',
            read_only=False,
            current_value=22,
            pending_value=None,
            fqdd='iDRAC.Embedded.1',
            group_id='SSH.1',
            lower_bound=1,
            upper_bound=65535)
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardEnumeration]['ok']},
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardString]['ok']},
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardInteger]['ok']}])

        idrac_settings = self.drac_client.list_idrac_settings(by_name=True)

        self.assertEqual(630, len(idrac_settings))

        # enumerable attribute
        self.assertIn('Info.1#Type', idrac_settings)
        self.assertEqual(expected_enum_attr, idrac_settings[
                         'Info.1#Type'])
        # string attribute
        self.assertIn('Info.1#Version', idrac_settings)
        self.assertEqual(expected_string_attr,
                         idrac_settings['Info.1#Version'])
        # integer attribute
        self.assertIn('SSH.1#Port', idrac_settings)
        self.assertEqual(expected_integer_attr, idrac_settings[
                         'SSH.1#Port'])

    def test_list_multi_idrac_settings_by_name(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        expected_enum_attr = idrac_card.iDRACCardEnumerableAttribute(
            name='Type',
            instance_id='iDRAC.Embedded.2#Info.1#Type',
            read_only=True,
            current_value='13G Monolithic',
            pending_value=None,
            fqdd='iDRAC.Embedded.2',
            group_id='Info.1',
            possible_values=['12G/13G', '12G Monolithic', '12G Modular',
                             '13G Monolithic', '13G Modular', '12G DCS',
                             '13G DCS'])
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardEnumeration]['ok']},
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardString]['ok']},
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardInteger]['ok']}])

        idrac_settings = self.drac_client.list_idrac_settings(
            by_name=True, fqdd_filter='iDRAC.Embedded.2')

        self.assertEqual(1, len(idrac_settings))

        # enumerable attribute
        self.assertIn('Info.1#Type', idrac_settings)
        self.assertEqual(expected_enum_attr, idrac_settings[
                         'Info.1#Type'])

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_set_idrac_settings(
            self, mock_requests, mock_invoke, mock_wait_until_idrac_is_ready):
        expected_selectors = {'CreationClassName': 'DCIM_iDRACCardService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:iDRACCardService',
                              'SystemCreationClassName': 'DCIM_ComputerSystem'}
        expected_properties = {'Target': 'iDRAC.Embedded.1',
                               'AttributeName': ['LDAP.1#GroupAttributeIsDN'],
                               'AttributeValue': ['Disabled']}
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardEnumeration]['ok']},
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardString]['ok']},
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardInteger]['ok']}])
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.iDracCardInvocations[uris.DCIM_iDRACCardService][
                'SetAttributes']['ok'])

        result = self.drac_client.set_idrac_settings(
            {'LDAP.1#GroupAttributeIsDN': 'Disabled'})

        self.assertEqual({'is_commit_required': True,
                          'is_reboot_required':
                              constants.RebootRequired.false},
                         result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_iDRACCardService, 'SetAttributes',
            expected_selectors, expected_properties)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_set_idrac_settings_with_valid_length_string(
            self, mock_requests, mock_invoke, mock_wait_until_idrac_is_ready):
        expected_selectors = {'CreationClassName': 'DCIM_iDRACCardService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:iDRACCardService',
                              'SystemCreationClassName': 'DCIM_ComputerSystem'}
        expected_properties = {'Target': 'iDRAC.Embedded.1',
                               'AttributeName': ['Users.16#Password'],
                               'AttributeValue': ['12345678901234567890']}
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardEnumeration]['ok']},
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardString]['ok']},
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardInteger]['ok']}])
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.iDracCardInvocations[uris.DCIM_iDRACCardService][
                'SetAttributes']['ok'])
        result = self.drac_client.set_idrac_settings(
            {'Users.16#Password': '12345678901234567890'})
        self.assertEqual({'is_commit_required': True,
                          'is_reboot_required':
                              constants.RebootRequired.false},
                         result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_iDRACCardService, 'SetAttributes',
            expected_selectors, expected_properties)

    def test_set_idrac_settings_with_too_long_string(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        expected_message = ("Attribute 'Password' cannot be set to "
                            "value '123456789012345678901'. It must be "
                            "between 0 and 20 characters in length.")
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardEnumeration]['ok']},
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardString]['ok']},
            {'text': test_utils.iDracCardEnumerations[
                uris.DCIM_iDRACCardInteger]['ok']}])
        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.set_idrac_settings,
            {'Users.16#Password': '123456789012345678901'})


class ClientiDRACCardChangesTestCase(base.BaseTest):

    def setUp(self):
        super(ClientiDRACCardChangesTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    @mock.patch.object(job.JobManagement, 'create_config_job', spec_set=True,
                       autospec=True)
    def test_commit_pending_idrac_changes(self, mock_create_config_job):
        self.drac_client.commit_pending_idrac_changes()

        mock_create_config_job.assert_called_once_with(
            mock.ANY,
            resource_uri=uris.DCIM_iDRACCardService,
            cim_creation_class_name='DCIM_iDRACCardService',
            cim_name='DCIM:iDRACCardService',
            target=dracclient.client.DRACClient.IDRAC_FQDD,
            reboot=False, start_time='TIME_NOW')

    @mock.patch.object(job.JobManagement, 'create_config_job', spec_set=True,
                       autospec=True)
    def test_commit_pending_idrac_changes_with_reboot(
            self, mock_create_config_job):

        self.drac_client.commit_pending_idrac_changes(
            reboot=True)

        mock_create_config_job.assert_called_once_with(
            mock.ANY,
            resource_uri=uris.DCIM_iDRACCardService,
            cim_creation_class_name='DCIM_iDRACCardService',
            cim_name='DCIM:iDRACCardService',
            target=dracclient.client.DRACClient.IDRAC_FQDD,
            reboot=True, start_time='TIME_NOW')

    @mock.patch.object(job.JobManagement, 'create_config_job', spec_set=True,
                       autospec=True)
    def test_commit_pending_idrac_changes_with_time(
            self, mock_create_config_job):
        timestamp = '20140924120101'
        self.drac_client.commit_pending_idrac_changes(
            start_time=timestamp)

        mock_create_config_job.assert_called_once_with(
            mock.ANY,
            resource_uri=uris.DCIM_iDRACCardService,
            cim_creation_class_name='DCIM_iDRACCardService',
            cim_name='DCIM:iDRACCardService',
            target=dracclient.client.DRACClient.IDRAC_FQDD,
            reboot=False, start_time=timestamp)

    @mock.patch.object(job.JobManagement, 'create_config_job', spec_set=True,
                       autospec=True)
    def test_commit_pending_idrac_changes_with_reboot_and_time(
            self, mock_create_config_job):

        timestamp = '20140924120101'
        self.drac_client.commit_pending_idrac_changes(
            reboot=True,
            start_time=timestamp)

        mock_create_config_job.assert_called_once_with(
            mock.ANY,
            resource_uri=uris.DCIM_iDRACCardService,
            cim_creation_class_name='DCIM_iDRACCardService',
            cim_name='DCIM:iDRACCardService',
            target=dracclient.client.DRACClient.IDRAC_FQDD,
            reboot=True, start_time=timestamp)

    @mock.patch.object(job.JobManagement, 'delete_pending_config',
                       spec_set=True, autospec=True)
    def test_abandon_pending_idrac_changes(self, mock_delete_pending_config):
        self.drac_client.abandon_pending_idrac_changes()

        mock_delete_pending_config.assert_called_once_with(
            mock.ANY,
            resource_uri=uris.DCIM_iDRACCardService,
            cim_creation_class_name='DCIM_iDRACCardService',
            cim_name='DCIM:iDRACCardService',
            target=dracclient.client.DRACClient.IDRAC_FQDD)


class ClientiDRACCardResetTestCase(base.BaseTest):

    def setUp(self):
        super(ClientiDRACCardResetTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    @mock.patch('dracclient.client.subprocess.call')
    def test_ping_host(self, mock_os_system):
        mock_os_system.return_value = 0
        response = self.drac_client._ping_host('127.0.0.1')
        self.assertEqual(mock_os_system.call_count, 1)
        self.assertEqual(True, response)

    @mock.patch('dracclient.client.subprocess.call')
    def test_ping_host_not_pingable(self, mock_os_system):
        mock_os_system.return_value = 1
        response = self.drac_client._ping_host('127.0.0.1')
        self.assertEqual(mock_os_system.call_count, 1)
        self.assertEqual(False, response)

    @mock.patch('dracclient.client.subprocess.call')
    def test_ping_host_name_not_known(self, mock_os_system):
        mock_os_system.return_value = 2
        response = self.drac_client._ping_host('127.0.0.1')
        self.assertEqual(mock_os_system.call_count, 1)
        self.assertEqual(False, response)

    @mock.patch('time.sleep')
    @mock.patch('dracclient.client.DRACClient._ping_host')
    def test_wait_for_host_alive(self, mock_ping_host, mock_sleep):
        total_calls = 5
        ping_count = 3
        mock_ping_host.return_value = True
        mock_sleep.return_value = None
        response = self.drac_client._wait_for_host_state(
            'hostname',
            alive=True,
            ping_count=ping_count,
            retries=total_calls)
        self.assertEqual(True, response)
        self.assertEqual(mock_sleep.call_count, ping_count)
        self.assertEqual(mock_ping_host.call_count, ping_count)

    @mock.patch('time.sleep')
    @mock.patch('dracclient.client.DRACClient._ping_host')
    def test_wait_for_host_alive_fail(self, mock_ping_host, mock_sleep):
        total_calls = 5
        ping_count = 3
        mock_ping_host.return_value = False
        mock_sleep.return_value = None
        response = self.drac_client._wait_for_host_state(
            'hostname',
            alive=True,
            ping_count=ping_count,
            retries=total_calls)
        self.assertEqual(False, response)
        self.assertEqual(mock_sleep.call_count, total_calls)
        self.assertEqual(mock_ping_host.call_count, total_calls)

    @mock.patch('time.sleep')
    @mock.patch('dracclient.client.DRACClient._ping_host')
    def test_wait_for_host_dead(self, mock_ping_host, mock_sleep):
        total_calls = 5
        ping_count = 3
        mock_ping_host.return_value = False
        mock_sleep.return_value = None
        response = self.drac_client._wait_for_host_state(
            'hostname',
            alive=False,
            ping_count=ping_count,
            retries=total_calls)
        self.assertEqual(True, response)
        self.assertEqual(mock_sleep.call_count, ping_count)
        self.assertEqual(mock_ping_host.call_count, ping_count)

    @mock.patch('time.sleep')
    @mock.patch('dracclient.client.DRACClient._ping_host')
    def test_wait_for_host_dead_fail(self, mock_ping_host, mock_sleep):
        total_calls = 5
        ping_count = 3
        mock_ping_host.return_value = True
        mock_sleep.return_value = None
        response = self.drac_client._wait_for_host_state(
            'hostname',
            alive=False,
            ping_count=ping_count,
            retries=total_calls)
        self.assertEqual(False, response)
        self.assertEqual(mock_sleep.call_count, total_calls)
        self.assertEqual(mock_ping_host.call_count, total_calls)

    @mock.patch('time.sleep')
    @mock.patch('dracclient.client.DRACClient._ping_host')
    def test_wait_for_host_alive_with_intermittent(
            self, mock_ping_host, mock_sleep):
        total_calls = 6
        ping_count = 3
        mock_ping_host.side_effect = [True, True, False, True, True, True]
        mock_sleep.return_value = None
        response = self.drac_client._wait_for_host_state(
            'hostname',
            alive=True,
            ping_count=ping_count,
            retries=total_calls)
        self.assertEqual(True, response)
        self.assertEqual(mock_sleep.call_count, total_calls)

    @mock.patch('time.sleep')
    @mock.patch('dracclient.client.DRACClient._ping_host')
    def test_wait_for_host_dead_with_intermittent(
            self, mock_ping_host, mock_sleep):
        total_calls = 6
        ping_count = 3
        mock_ping_host.side_effect = [False, False, True, False, False, False]
        mock_sleep.return_value = None
        response = self.drac_client._wait_for_host_state(
            'hostname',
            alive=False,
            ping_count=ping_count,
            retries=total_calls)
        self.assertEqual(True, response)
        self.assertEqual(mock_sleep.call_count, total_calls)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_reset_idrac(self, mock_invoke):
        expected_selectors = {
            'CreationClassName': "DCIM_iDRACCardService",
            'Name': "DCIM:iDRACCardService",
            'SystemCreationClassName': 'DCIM_ComputerSystem',
            'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Force': '0'}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.iDracCardInvocations[uris.DCIM_iDRACCardService][
                'iDRACReset']['ok'])

        result = self.drac_client.reset_idrac()

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_iDRACCardService, 'iDRACReset',
            expected_selectors, expected_properties,
            check_return_value=False)
        self.assertTrue(result)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_reset_idrac_force(self, mock_invoke):
        expected_selectors = {
            'CreationClassName': "DCIM_iDRACCardService",
            'Name': "DCIM:iDRACCardService",
            'SystemCreationClassName': 'DCIM_ComputerSystem',
            'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Force': '1'}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.iDracCardInvocations[uris.DCIM_iDRACCardService][
                'iDRACReset']['ok'])

        result = self.drac_client.reset_idrac(force=True)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_iDRACCardService, 'iDRACReset',
            expected_selectors, expected_properties,
            check_return_value=False)
        self.assertTrue(result)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_reset_idrac_bad_result(self, mock_invoke):
        expected_selectors = {
            'CreationClassName': "DCIM_iDRACCardService",
            'Name': "DCIM:iDRACCardService",
            'SystemCreationClassName': 'DCIM_ComputerSystem',
            'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Force': '0'}
        expected_message = ("Failed to reset iDRAC")
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.iDracCardInvocations[uris.DCIM_iDRACCardService][
                'iDRACReset']['error'])

        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.reset_idrac)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_iDRACCardService, 'iDRACReset',
            expected_selectors, expected_properties,
            check_return_value=False)

    @mock.patch('time.sleep')
    @mock.patch('dracclient.client.WSManClient.wait_until_idrac_is_ready')
    @mock.patch('dracclient.client.DRACClient._wait_for_host_state')
    @mock.patch(
        'dracclient.client.idrac_card.iDRACCardConfiguration.reset_idrac')
    def test_reset_idrac_wait(
            self,
            mock_reset_idrac,
            mock_wait_for_host_state,
            mock_wait_until_idrac_is_ready,
            mock_sleep):
        mock_reset_idrac.return_value = True
        mock_wait_for_host_state.side_effect = [True, True]
        mock_wait_until_idrac_is_ready.return_value = True
        mock_sleep.return_value = None

        self.drac_client.reset_idrac(wait=True)

        mock_reset_idrac.assert_called_once()
        self.assertEqual(mock_wait_for_host_state.call_count, 2)
        mock_wait_until_idrac_is_ready.assert_called_once()

    @mock.patch('time.sleep')
    @mock.patch('dracclient.client.WSManClient.wait_until_idrac_is_ready')
    @mock.patch('dracclient.client.DRACClient._wait_for_host_state')
    @mock.patch(
        'dracclient.client.idrac_card.iDRACCardConfiguration.reset_idrac')
    def test_reset_idrac_wait_failed_reset(
            self,
            mock_reset_idrac,
            mock_wait_for_host_state,
            mock_wait_until_idrac_is_ready,
            mock_sleep):
        mock_reset_idrac.return_value = False
        mock_wait_for_host_state.side_effect = [True, True]
        mock_wait_until_idrac_is_ready.return_value = False
        mock_sleep.return_value = None
        expected_message = ("Failed to reset iDRAC")

        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.reset_idrac, wait=True)

        mock_reset_idrac.assert_called_once()
        mock_wait_for_host_state.assert_not_called()
        mock_wait_until_idrac_is_ready.assert_not_called()

    @mock.patch('time.sleep')
    @mock.patch('dracclient.client.WSManClient.wait_until_idrac_is_ready')
    @mock.patch('dracclient.client.DRACClient._wait_for_host_state')
    @mock.patch(
        'dracclient.client.idrac_card.iDRACCardConfiguration.reset_idrac')
    def test_reset_idrac_fail_wait_not_pingable(
            self,
            mock_reset_idrac,
            mock_wait_for_host_state,
            mock_wait_until_idrac_is_ready,
            mock_sleep):
        mock_reset_idrac.return_value = True
        mock_wait_for_host_state.side_effect = [False, True]
        mock_wait_until_idrac_is_ready.return_value = True
        mock_sleep.return_value = None
        expected_message = (
            "Timed out waiting for the 1.2.3.4 iDRAC to become not pingable")

        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.reset_idrac, wait=True)

        mock_reset_idrac.assert_called_once()
        mock_wait_for_host_state.assert_called_once()
        mock_wait_until_idrac_is_ready.assert_not_called()

    @mock.patch('time.sleep')
    @mock.patch('dracclient.client.WSManClient.wait_until_idrac_is_ready')
    @mock.patch('dracclient.client.DRACClient._wait_for_host_state')
    @mock.patch(
        'dracclient.client.idrac_card.iDRACCardConfiguration.reset_idrac')
    def test_reset_idrac_fail_wait_pingable(
            self,
            mock_reset_idrac,
            mock_wait_for_host_state,
            mock_wait_until_idrac_is_ready,
            mock_sleep):
        mock_reset_idrac.return_value = True
        mock_wait_for_host_state.side_effect = [True, False]
        mock_wait_until_idrac_is_ready.return_value = True
        mock_sleep.return_value = None
        expected_message = (
            "Timed out waiting for the 1.2.3.4 iDRAC to become pingable")

        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.reset_idrac, wait=True)

        mock_reset_idrac.assert_called_once()
        self.assertEqual(mock_wait_for_host_state.call_count, 2)
        mock_wait_until_idrac_is_ready.assert_not_called()
