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

import requests_mock

import dracclient.client
from dracclient.resources import idrac_card
from dracclient.resources import uris
from dracclient.tests import base
from dracclient.tests import utils as test_utils


class ClientiDRACCardConfigurationTestCase(base.BaseTest):

    def setUp(self):
        super(ClientiDRACCardConfigurationTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    @requests_mock.Mocker()
    def test_list_idrac_settings(self, mock_requests):
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

        self.assertEqual(630, len(idrac_settings))
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
