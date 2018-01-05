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

import mock
import requests_mock

import dracclient.client
from dracclient import constants
from dracclient import exceptions
from dracclient.resources import uris
from dracclient.tests import base
from dracclient.tests import utils as test_utils


@requests_mock.Mocker()
class WSManClientTestCase(base.BaseTest):

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_enumerate(self, mock_requests, mock_wait_until_idrac_is_ready):
        mock_requests.post('https://1.2.3.4:443/wsman',
                           text='<result>yay!</result>')

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        resp = client.enumerate('http://resource')
        mock_wait_until_idrac_is_ready.assert_called_once_with(client)
        self.assertEqual('yay!', resp.text)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_enumerate_without_wait_for_idrac(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        mock_requests.post('https://1.2.3.4:443/wsman',
                           text='<result>yay!</result>')

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        resp = client.enumerate('http://resource', wait_for_idrac=False)
        self.assertFalse(mock_wait_until_idrac_is_ready.called)
        self.assertEqual('yay!', resp.text)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_invoke(self, mock_requests, mock_wait_until_idrac_is_ready):
        xml = """
<response xmlns:n1="http://resource">
    <n1:ReturnValue>42</n1:ReturnValue>
    <result>yay!</result>
</response>
"""  # noqa
        mock_requests.post('https://1.2.3.4:443/wsman', text=xml)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        resp = client.invoke('http://resource', 'Foo')
        mock_wait_until_idrac_is_ready.assert_called_once_with(client)
        self.assertEqual('yay!', resp.find('result').text)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_invoke_without_wait_for_idrac(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        xml = """
<response xmlns:n1="http://resource">
    <n1:ReturnValue>42</n1:ReturnValue>
    <result>yay!</result>
</response>
"""  # noqa
        mock_requests.post('https://1.2.3.4:443/wsman', text=xml)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        resp = client.invoke('http://resource', 'Foo', wait_for_idrac=False)
        self.assertFalse(mock_wait_until_idrac_is_ready.called)
        self.assertEqual('yay!', resp.find('result').text)

    def test_invoke_with_expected_return_value(self, mock_requests):
        xml = """
<response xmlns:n1="http://resource">
    <n1:ReturnValue>42</n1:ReturnValue>
    <result>yay!</result>
</response>
"""  # noqa
        mock_requests.post('https://1.2.3.4:443/wsman', text=xml)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        resp = client.invoke('http://resource', 'Foo',
                             expected_return_value='42', wait_for_idrac=False)
        self.assertEqual('yay!', resp.find('result').text)

    def test_invoke_with_error_return_value(self, mock_requests):
        xml = """
<response xmlns:n1="http://resource">
    <n1:ReturnValue>2</n1:ReturnValue>
    <result>yay!</result>
</response>
"""  # noqa
        mock_requests.post('https://1.2.3.4:443/wsman', text=xml)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        self.assertRaises(exceptions.DRACOperationFailed, client.invoke,
                          'http://resource', 'Foo', wait_for_idrac=False)

    def test_invoke_with_unchecked_return_value(self, mock_requests):
        xml = """
<response xmlns:n1="http://resource">
    <n1:ReturnValue>2</n1:ReturnValue>
    <result>yay!</result>
</response>
"""  # noqa
        mock_requests.post('https://1.2.3.4:443/wsman', text=xml)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        resp = client.invoke('http://resource', 'Foo',
                             wait_for_idrac=False, check_return_value=False)
        self.assertEqual('yay!', resp.find('result').text)

    def test_invoke_with_unexpected_return_value(self, mock_requests):
        xml = """
<response xmlns:n1="http://resource">
    <n1:ReturnValue>42</n1:ReturnValue>
    <result>yay!</result>
</response>
"""  # noqa
        mock_requests.post('https://1.2.3.4:443/wsman', text=xml)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        self.assertRaises(exceptions.DRACUnexpectedReturnValue, client.invoke,
                          'http://resource', 'Foo',
                          expected_return_value='4242', wait_for_idrac=False)

    def test_is_idrac_ready_ready(self, mock_requests):
        expected_text = test_utils.LifecycleControllerInvocations[
            uris.DCIM_LCService]['GetRemoteServicesAPIStatus']['is_ready']
        mock_requests.post('https://1.2.3.4:443/wsman',
                           text=expected_text)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        self.assertTrue(client.is_idrac_ready())

    def test_is_idrac_ready_not_ready(self, mock_requests):
        expected_text = test_utils.LifecycleControllerInvocations[
            uris.DCIM_LCService]['GetRemoteServicesAPIStatus']['is_not_ready']
        mock_requests.post('https://1.2.3.4:443/wsman',
                           text=expected_text)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        self.assertFalse(client.is_idrac_ready())

    @mock.patch.object(dracclient.client.WSManClient, 'is_idrac_ready',
                       autospec=True)
    @mock.patch('time.sleep', autospec=True)
    def test_wait_until_idrac_is_ready_with_none_arguments(
            self, mock_requests, mock_ts, mock_is_idrac_ready):
        ready_retries = 2
        ready_retry_delay = 1

        side_effect = (ready_retries - 1) * [False]
        side_effect.append(True)
        mock_is_idrac_ready.side_effect = side_effect

        fake_endpoint = test_utils.FAKE_ENDPOINT.copy()
        fake_endpoint['ready_retries'] = ready_retries
        fake_endpoint['ready_retry_delay'] = ready_retry_delay

        client = dracclient.client.WSManClient(**fake_endpoint)
        client.wait_until_idrac_is_ready(retries=None, retry_delay=None)

        self.assertEqual(mock_is_idrac_ready.call_count, ready_retries)
        self.assertEqual(mock_ts.call_count, ready_retries - 1)
        mock_ts.assert_called_with(ready_retry_delay)

    @mock.patch.object(dracclient.client.WSManClient, 'is_idrac_ready',
                       autospec=True)
    @mock.patch('time.sleep', autospec=True)
    def test_wait_until_idrac_is_ready_with_non_none_arguments(
            self, mock_requests, mock_ts, mock_is_idrac_ready):
        retries = 2
        self.assertNotEqual(retries, constants.DEFAULT_IDRAC_IS_READY_RETRIES)

        retry_delay = 1
        self.assertNotEqual(
            retry_delay, constants.DEFAULT_IDRAC_IS_READY_RETRY_DELAY_SEC)

        side_effect = (retries - 1) * [False]
        side_effect.append(True)
        mock_is_idrac_ready.side_effect = side_effect

        fake_endpoint = test_utils.FAKE_ENDPOINT.copy()
        fake_endpoint['ready_retries'] = (
            constants.DEFAULT_IDRAC_IS_READY_RETRIES)
        fake_endpoint['ready_retry_delay'] = (
            constants.DEFAULT_IDRAC_IS_READY_RETRY_DELAY_SEC)

        client = dracclient.client.WSManClient(**fake_endpoint)
        client.wait_until_idrac_is_ready(retries, retry_delay)

        self.assertEqual(mock_is_idrac_ready.call_count, retries)
        self.assertEqual(mock_ts.call_count, retries - 1)
        mock_ts.assert_called_with(retry_delay)

    def test_wait_until_idrac_is_ready_ready(self, mock_requests):
        expected_text = test_utils.LifecycleControllerInvocations[
            uris.DCIM_LCService]['GetRemoteServicesAPIStatus']['is_ready']
        mock_requests.post('https://1.2.3.4:443/wsman',
                           text=expected_text)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)

        try:
            client.wait_until_idrac_is_ready()
        except exceptions.DRACOperationFailed:
            self.fail('wait_until_idrac_is_ready() timed out when it should '
                      'not have!')

    @mock.patch('time.sleep', autospec=True)
    def test_wait_until_idrac_is_ready_timeout(self,
                                               mock_requests,
                                               mock_ts):
        expected_text = test_utils.LifecycleControllerInvocations[
            uris.DCIM_LCService]['GetRemoteServicesAPIStatus']['is_not_ready']
        mock_requests.post('https://1.2.3.4:443/wsman',
                           text=expected_text)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        self.assertRaises(exceptions.DRACOperationFailed,
                          client.wait_until_idrac_is_ready)
