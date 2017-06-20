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
from dracclient import exceptions
from dracclient.resources import uris
from dracclient.tests import base
from dracclient.tests import utils as test_utils


@requests_mock.Mocker()
class WSManClientTestCase(base.BaseTest):

    def test_enumerate(self, mock_requests):
        mock_requests.post('https://1.2.3.4:443/wsman',
                           text='<result>yay!</result>')

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        resp = client.enumerate('http://resource')
        self.assertEqual('yay!', resp.text)

    def test_invoke(self, mock_requests):
        xml = """
<response xmlns:n1="http://resource">
    <n1:ReturnValue>42</n1:ReturnValue>
    <result>yay!</result>
</response>
"""  # noqa
        mock_requests.post('https://1.2.3.4:443/wsman', text=xml)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        resp = client.invoke('http://resource', 'Foo')
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
                             expected_return_value='42')
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
                          'http://resource', 'Foo')

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
                          expected_return_value='4242')

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
