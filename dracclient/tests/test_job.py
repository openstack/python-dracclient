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
import requests_mock

import dracclient.client
from dracclient import exceptions
import dracclient.resources.job
from dracclient.resources import uris
from dracclient.tests import base
from dracclient.tests import utils as test_utils
from dracclient import utils


class ClientJobManagementTestCase(base.BaseTest):

    def setUp(self):
        super(ClientJobManagementTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    @requests_mock.Mocker()
    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_list_jobs(self, mock_requests, mock_wait_until_idrac_is_ready):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.JobEnumerations[uris.DCIM_LifecycleJob]['ok'])

        jobs = self.drac_client.list_jobs()

        self.assertEqual(6, len(jobs))

    @mock.patch.object(dracclient.client.WSManClient, 'enumerate',
                       spec_set=True, autospec=True)
    def test_list_jobs_only_unfinished(self, mock_enumerate):
        expected_filter_query = ('select * from DCIM_LifecycleJob '
                                 'where Name != "CLEARALL" and '
                                 'JobStatus != "Reboot Completed" and '
                                 'JobStatus != "Reboot Failed" and '
                                 'JobStatus != "Completed" and '
                                 'JobStatus != "Completed with Errors" and '
                                 'JobStatus != "Failed"')
        mock_enumerate.return_value = lxml.etree.fromstring(
            test_utils.JobEnumerations[uris.DCIM_LifecycleJob]['ok'])

        self.drac_client.list_jobs(only_unfinished=True)

        mock_enumerate.assert_called_once_with(
            mock.ANY, uris.DCIM_LifecycleJob,
            filter_query=expected_filter_query)

    @mock.patch.object(dracclient.client.WSManClient, 'enumerate',
                       spec_set=True, autospec=True)
    def test_get_job(self, mock_enumerate):
        expected_filter_query = ('select * from DCIM_LifecycleJob'
                                 ' where InstanceID="42"')
        # NOTE: This is the first job in the xml. Filtering the job is the
        #       responsibility of the controller, so not testing it.
        expected_job = dracclient.resources.job.Job(id='JID_CLEARALL',
                                                    name='CLEARALL',
                                                    start_time='TIME_NA',
                                                    until_time='TIME_NA',
                                                    message='NA',
                                                    status='Pending',
                                                    percent_complete='0')
        mock_enumerate.return_value = lxml.etree.fromstring(
            test_utils.JobEnumerations[uris.DCIM_LifecycleJob]['ok'])

        job = self.drac_client.get_job(42)

        mock_enumerate.assert_called_once_with(
            mock.ANY, uris.DCIM_LifecycleJob,
            filter_query=expected_filter_query)
        self.assertEqual(expected_job, job)

    @mock.patch.object(dracclient.client.WSManClient, 'enumerate',
                       spec_set=True, autospec=True)
    def test_get_job_not_found(self, mock_enumerate):
        expected_filter_query = ('select * from DCIM_LifecycleJob'
                                 ' where InstanceID="42"')
        mock_enumerate.return_value = lxml.etree.fromstring(
            test_utils.JobEnumerations[uris.DCIM_LifecycleJob]['not_found'])

        job = self.drac_client.get_job(42)

        mock_enumerate.assert_called_once_with(
            mock.ANY, uris.DCIM_LifecycleJob,
            filter_query=expected_filter_query)
        self.assertIsNone(job)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_delete_jobs_all(self, mock_invoke):
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'idrac',
                              'CreationClassName': 'DCIM_JobService',
                              'Name': 'JobService'}
        expected_properties = {'JobID': 'JID_CLEARALL'}

        self.drac_client.delete_jobs()

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_JobService, 'DeleteJobQueue',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_delete_jobs_force(self, mock_invoke):
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'idrac',
                              'CreationClassName': 'DCIM_JobService',
                              'Name': 'JobService'}
        expected_properties = {'JobID': 'JID_CLEARALL_FORCE'}

        self.drac_client.delete_jobs(['JID_CLEARALL_FORCE'])

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_JobService, 'DeleteJobQueue',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_delete_jobs_one(self, mock_invoke):
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'idrac',
                              'CreationClassName': 'DCIM_JobService',
                              'Name': 'JobService'}
        expected_properties = {'JobID': 'JID_442507917525'}

        self.drac_client.delete_jobs(['JID_442507917525'])

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_JobService, 'DeleteJobQueue',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_delete_jobs_multi(self, mock_invoke):
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'idrac',
                              'CreationClassName': 'DCIM_JobService',
                              'Name': 'JobService'}

        self.drac_client.delete_jobs(['JID_442507917525',
                                      'JID_442507917526'])

        calls_expected = [
            mock.call(mock.ANY,
                      uris.DCIM_JobService,
                      'DeleteJobQueue',
                      expected_selectors,
                      {'JobID': 'JID_442507917525'},
                      expected_return_value=utils.RET_SUCCESS),
            mock.call(mock.ANY,
                      uris.DCIM_JobService,
                      'DeleteJobQueue',
                      expected_selectors,
                      {'JobID': 'JID_442507917526'},
                      expected_return_value=utils.RET_SUCCESS)]
        mock_invoke.assert_has_calls(calls_expected)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_delete_jobs_none(self, mock_invoke):
        self.drac_client.delete_jobs(None)
        self.assertFalse(mock_invoke.called)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_delete_jobs_empty_list(self, mock_invoke):
        self.drac_client.delete_jobs([])
        self.assertFalse(mock_invoke.called)

    @requests_mock.Mocker()
    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_delete_job_not_found(
            self, mock_requests,
            mock_wait_until_idrac_is_ready):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.JobService[uris.DCIM_JobService][
                'DeleteJobQueue']['error'])
        self.assertRaises(
            exceptions.DRACOperationFailed,
            self.drac_client.delete_jobs,
            ['JID_1234'])

    @requests_mock.Mocker()
    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_delete_some_jobs_not_found(
            self, mock_requests,
            mock_wait_until_idrac_is_ready):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            [{'text': test_utils.JobService[uris.DCIM_JobService][
                'DeleteJobQueue']['error']},
             {'text': test_utils.JobService[uris.DCIM_JobService][
                 'DeleteJobQueue']['ok']}])

        self.assertRaises(
            exceptions.DRACOperationFailed,
            self.drac_client.delete_jobs,
            ['JID_1234', 'JID_442507917525'])

        self.assertEqual(mock_requests.call_count, 2)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_create_config_job(self, mock_invoke):
        cim_creation_class_name = 'DCIM_BIOSService'
        cim_name = 'DCIM:BIOSService'
        target = 'BIOS.Setup.1-1'
        expected_selectors = {'CreationClassName': cim_creation_class_name,
                              'Name': cim_name,
                              'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Target': target,
                               'ScheduledStartTime': 'TIME_NOW'}

        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.JobInvocations[uris.DCIM_BIOSService][
                'CreateTargetedConfigJob']['ok'])

        job_id = self.drac_client.create_config_job(
            uris.DCIM_BIOSService, cim_creation_class_name, cim_name, target)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_BIOSService, 'CreateTargetedConfigJob',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_CREATED)
        self.assertEqual('JID_442507917525', job_id)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_create_config_job_with_start_time(self, mock_invoke):
        cim_creation_class_name = 'DCIM_BIOSService'
        cim_name = 'DCIM:BIOSService'
        target = 'BIOS.Setup.1-1'
        start_time = "20140924120105"
        expected_selectors = {'CreationClassName': cim_creation_class_name,
                              'Name': cim_name,
                              'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Target': target,
                               'ScheduledStartTime': start_time}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.JobInvocations[uris.DCIM_BIOSService][
                'CreateTargetedConfigJob']['ok'])

        job_id = self.drac_client.create_config_job(
            uris.DCIM_BIOSService, cim_creation_class_name, cim_name, target,
            start_time=start_time)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_BIOSService, 'CreateTargetedConfigJob',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_CREATED)
        self.assertEqual('JID_442507917525', job_id)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_create_config_job_with_no_start_time(self, mock_invoke):
        cim_creation_class_name = 'DCIM_BIOSService'
        cim_name = 'DCIM:BIOSService'
        target = 'BIOS.Setup.1-1'
        start_time = None
        expected_selectors = {'CreationClassName': cim_creation_class_name,
                              'Name': cim_name,
                              'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Target': target}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.JobInvocations[uris.DCIM_BIOSService][
                'CreateTargetedConfigJob']['ok'])

        job_id = self.drac_client.create_config_job(
            uris.DCIM_BIOSService, cim_creation_class_name, cim_name, target,
            start_time=start_time)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_BIOSService, 'CreateTargetedConfigJob',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_CREATED)
        self.assertEqual('JID_442507917525', job_id)

    @requests_mock.Mocker()
    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_create_config_job_failed(self, mock_requests,
                                      mock_wait_until_idrac_is_ready):
        cim_creation_class_name = 'DCIM_BIOSService'
        cim_name = 'DCIM:BIOSService'
        target = 'BIOS.Setup.1-1'
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.JobInvocations[uris.DCIM_BIOSService][
                'CreateTargetedConfigJob']['error'])

        self.assertRaises(
            exceptions.DRACOperationFailed, self.drac_client.create_config_job,
            uris.DCIM_BIOSService, cim_creation_class_name, cim_name, target)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_create_config_job_with_reboot(self, mock_invoke):
        cim_creation_class_name = 'DCIM_BIOSService'
        cim_name = 'DCIM:BIOSService'
        target = 'BIOS.Setup.1-1'
        expected_selectors = {'CreationClassName': cim_creation_class_name,
                              'Name': cim_name,
                              'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Target': target,
                               'RebootJobType': '3',
                               'ScheduledStartTime': 'TIME_NOW'}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.JobInvocations[uris.DCIM_BIOSService][
                'CreateTargetedConfigJob']['ok'])

        job_id = self.drac_client.create_config_job(
            uris.DCIM_BIOSService, cim_creation_class_name, cim_name, target,
            reboot=True, realtime=False)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_BIOSService, 'CreateTargetedConfigJob',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_CREATED)
        self.assertEqual('JID_442507917525', job_id)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_create_config_job_with_realtime(self, mock_invoke):
        cim_creation_class_name = 'DCIM_BIOSService'
        cim_name = 'DCIM:BIOSService'
        target = 'BIOS.Setup.1-1'
        expected_selectors = {'CreationClassName': cim_creation_class_name,
                              'Name': cim_name,
                              'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Target': target,
                               'ScheduledStartTime': 'TIME_NOW',
                               'RealTime': '1'}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.JobInvocations[uris.DCIM_BIOSService][
                'CreateTargetedConfigJob']['ok'])

        job_id = self.drac_client.create_config_job(
            uris.DCIM_BIOSService, cim_creation_class_name, cim_name, target,
            reboot=False, realtime=True)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_BIOSService, 'CreateTargetedConfigJob',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_CREATED)
        self.assertEqual('JID_442507917525', job_id)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_create_reboot_job(self, mock_invoke):
        expected_selectors = {
            'SystemCreationClassName': 'DCIM_ComputerSystem',
            'SystemName': 'idrac',
            'CreationClassName': 'DCIM_JobService',
            'Name': 'JobService'}
        expected_properties = {'RebootJobType': '3'}
        self.drac_client.create_reboot_job()

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_JobService, 'CreateRebootJob',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_CREATED)

    def test_create_reboot_job_bad_type(self):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_reboot_job, 'BAD REBOOT TYPE')

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_delete_pending_config(self, mock_invoke):
        cim_creation_class_name = 'DCIM_BIOSService'
        cim_name = 'DCIM:BIOSService'
        target = 'BIOS.Setup.1-1'
        expected_selectors = {'CreationClassName': cim_creation_class_name,
                              'Name': cim_name,
                              'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Target': target}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.JobInvocations[uris.DCIM_BIOSService][
                'DeletePendingConfiguration']['ok'])

        self.drac_client.delete_pending_config(
            uris.DCIM_BIOSService, cim_creation_class_name, cim_name, target)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_BIOSService, 'DeletePendingConfiguration',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @requests_mock.Mocker()
    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_delete_pending_config_failed(self, mock_requests,
                                          mock_wait_until_idrac_is_ready):
        cim_creation_class_name = 'DCIM_BIOSService'
        cim_name = 'DCIM:BIOSService'
        target = 'BIOS.Setup.1-1'
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.JobInvocations[uris.DCIM_BIOSService][
                'DeletePendingConfiguration']['error'])

        self.assertRaises(
            exceptions.DRACOperationFailed,
            self.drac_client.delete_pending_config, uris.DCIM_BIOSService,
            cim_creation_class_name, cim_name, target)


class ClientJobScheduleTestCase(base.BaseTest):
    def setUp(self):
        super(ClientJobScheduleTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    def _test_schedule_job_execution(self,
                                     mock_invoke,
                                     job_ids,
                                     start_time,
                                     expected_properties):
        expected_selectors = {
            'SystemCreationClassName': 'DCIM_ComputerSystem',
            'SystemName': 'idrac',
            'CreationClassName': 'DCIM_JobService',
            'Name': 'JobService'}

        if start_time is None:
            self.drac_client.schedule_job_execution(job_ids)
        else:
            self.drac_client.schedule_job_execution(job_ids, start_time)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_JobService, 'SetupJobQueue',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_schedule_job_execution_one_job(self, mock_invoke):
        job_ids = ['JID_442507917525']
        expected_properties = {'StartTimeInterval': 'TIME_NOW',
                               'JobArray': job_ids}

        self._test_schedule_job_execution(mock_invoke, job_ids, None,
                                          expected_properties)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_schedule_job_execution_multi_job(self, mock_invoke):
        job_ids = ['JID_442507917525', 'JID_442507917526']
        expected_properties = {'StartTimeInterval': 'TIME_NOW',
                               'JobArray': job_ids}
        self._test_schedule_job_execution(mock_invoke, job_ids, None,
                                          expected_properties)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_schedule_job_execution_one_job_with_time(self, mock_invoke):
        job_ids = ['JID_442507917525']
        timestamp = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        expected_properties = {'StartTimeInterval': timestamp,
                               'JobArray': job_ids}
        self._test_schedule_job_execution(mock_invoke, job_ids, timestamp,
                                          expected_properties)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_schedule_job_execution_multi_job_with_time(self, mock_invoke):
        job_ids = ['JID_442507917525', 'JID_442507917526']
        timestamp = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        expected_properties = {'StartTimeInterval': timestamp,
                               'JobArray': job_ids}
        self._test_schedule_job_execution(mock_invoke, job_ids, timestamp,
                                          expected_properties)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke')
    def test_schedule_job_execution_no_jobs(self, mock_invoke):
        self.drac_client.schedule_job_execution(job_ids=[])
        mock_invoke.assert_not_called()
