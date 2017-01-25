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
import uuid

import lxml.etree
import lxml.objectify
import mock
import requests_mock

from dracclient import exceptions
from dracclient.tests import base
from dracclient.tests import utils as test_utils
import dracclient.wsman


class ClientTestCase(base.BaseTest):

    def setUp(self):
        super(ClientTestCase, self).setUp()
        self.client = dracclient.wsman.Client(**test_utils.FAKE_ENDPOINT)

    @requests_mock.Mocker()
    def test_enumerate(self, mock_requests):
        expected_resp = '<result>yay!</result>'
        mock_requests.post('https://1.2.3.4:443/wsman', text=expected_resp)

        resp = self.client.enumerate('resource', auto_pull=False)
        self.assertEqual('yay!', resp.text)

    def test_enumerate_with_request_failure(self):
        self.client = dracclient.wsman.Client('malformed://^@*', 'user',
                                              'pass')

        self.assertRaises(exceptions.WSManRequestFailure,
                          self.client.enumerate, 'resource')

    @requests_mock.Mocker()
    def test_enumerate_with_invalid_status_code(self, mock_requests):
        mock_requests.post('https://1.2.3.4:443/wsman', status_code=500,
                           reason='dumb request')

        self.assertRaises(exceptions.WSManInvalidResponse,
                          self.client.enumerate, 'resource')

    @requests_mock.Mocker()
    def test_enumerate_with_auto_pull(self, mock_requests):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            [{'text': test_utils.WSManEnumerations['context'][0]},
             {'text': test_utils.WSManEnumerations['context'][1]},
             {'text': test_utils.WSManEnumerations['context'][2]},
             {'text': test_utils.WSManEnumerations['context'][3]}])

        resp_xml = self.client.enumerate('FooResource')

        foo_resource_uri = 'http://FooResource'
        bar_resource_uri = 'http://BarResource'
        self.assertEqual(
            4, len(resp_xml.findall('.//{%s}FooResource' % foo_resource_uri)))
        self.assertEqual(
            1, len(resp_xml.findall('.//{%s}BazResource' % bar_resource_uri)))
        self.assertEqual(
            0, len(resp_xml.findall(
                './/{%s}EnumerationContext' % dracclient.wsman.NS_WSMAN_ENUM)))

    @requests_mock.Mocker()
    @mock.patch.object(dracclient.wsman.Client, 'pull', autospec=True)
    def test_enumerate_with_auto_pull_without_optimization(self, mock_requests,
                                                           mock_pull):
        mock_requests.post('https://1.2.3.4:443/wsman',
                           text=test_utils.WSManEnumerations['context'][0])
        mock_pull.return_value = lxml.etree.fromstring(
            test_utils.WSManEnumerations['context'][3])

        self.client.enumerate('FooResource', optimization=False, max_elems=42)

        mock_pull.assert_called_once_with(self.client, 'FooResource',
                                          'enum-context-uuid', 42)

    @requests_mock.Mocker()
    def test_pull(self, mock_requests):
        expected_resp = '<result>yay!</result>'
        mock_requests.post('https://1.2.3.4:443/wsman', text=expected_resp)

        resp = self.client.pull('resource', 'context-uuid')

        self.assertEqual('yay!', resp.text)

    @requests_mock.Mocker()
    def test_invoke(self, mock_requests):
        expected_resp = '<result>yay!</result>'
        mock_requests.post('https://1.2.3.4:443/wsman', text=expected_resp)

        resp = self.client.invoke('http://resource', 'method',
                                  {'selector': 'foo'}, {'property': 'bar'})

        self.assertEqual('yay!', resp.text)


class PayloadTestCase(base.BaseTest):

    def setUp(self):
        super(PayloadTestCase, self).setUp()
        dracclient.wsman.NS_MAP = collections.OrderedDict([
            ('s', dracclient.wsman.NS_SOAP_ENV),
            ('wsa', dracclient.wsman.NS_WS_ADDR),
            ('wsman', dracclient.wsman.NS_WSMAN)])

    @mock.patch.object(uuid, 'uuid4', autospec=True)
    def test_build_enum(self, mock_uuid):
        expected_payload = """<?xml version="1.0" ?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
            xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <wsa:To s:mustUnderstand="true">http://host:443/wsman</wsa:To>
        <wsman:ResourceURI s:mustUnderstand="true">http://resource_uri</wsman:ResourceURI>
        <wsa:MessageID s:mustUnderstand="true">uuid:1234-12</wsa:MessageID>
        <wsa:ReplyTo>
            <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
        </wsa:ReplyTo>
        <wsa:Action s:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/09/enumeration/Enumerate</wsa:Action>
    </s:Header>
    <s:Body>
        <wsen:Enumerate xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration">
            <wsman:OptimizeEnumeration/>
            <wsman:MaxElements>100</wsman:MaxElements>
        </wsen:Enumerate>
    </s:Body>
</s:Envelope>
"""  # noqa
        expected_payload_obj = lxml.objectify.fromstring(expected_payload)

        mock_uuid.return_value = '1234-12'
        payload = dracclient.wsman._EnumeratePayload(
            'http://host:443/wsman', 'http://resource_uri').build()
        payload_obj = lxml.objectify.fromstring(payload)

        self.assertEqual(lxml.etree.tostring(expected_payload_obj),
                         lxml.etree.tostring(payload_obj))

    def test_enumerate_without_optimization(self):
        payload = dracclient.wsman._EnumeratePayload(
            'http://host:443/wsman', 'http://resource_uri', optimization=False,
            max_elems=42).build()
        payload_xml = lxml.etree.fromstring(payload)

        optimize_enum_elems = payload_xml.findall(
            './/{%s}OptimizeEnumeration' % dracclient.wsman.NS_WSMAN)
        max_elem_elems = payload_xml.findall(
            './/{%s}MaxElements' % dracclient.wsman.NS_WSMAN)
        self.assertEqual([], optimize_enum_elems)
        self.assertEqual([], max_elem_elems)

    @mock.patch.object(uuid, 'uuid4', autospec=True)
    def test_build_enum_with_filter(self, mock_uuid):
        expected_payload = """<?xml version="1.0" ?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
            xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <wsa:To s:mustUnderstand="true">http://host:443/wsman</wsa:To>
        <wsman:ResourceURI s:mustUnderstand="true">http://resource_uri</wsman:ResourceURI>
        <wsa:MessageID s:mustUnderstand="true">uuid:1234-12</wsa:MessageID>
        <wsa:ReplyTo>
            <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
        </wsa:ReplyTo>
        <wsa:Action s:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/09/enumeration/Enumerate</wsa:Action>
    </s:Header>
    <s:Body>
        <wsen:Enumerate xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration">
            <wsman:Filter Dialect="http://schemas.dmtf.org/wbem/cql/1/dsp0202.pdf">DROP TABLE users</wsman:Filter>
            <wsman:OptimizeEnumeration/>
            <wsman:MaxElements>100</wsman:MaxElements>
        </wsen:Enumerate>
    </s:Body>
</s:Envelope>
"""  # noqa
        expected_payload_obj = lxml.objectify.fromstring(expected_payload)

        mock_uuid.return_value = '1234-12'
        payload = dracclient.wsman._EnumeratePayload(
            'http://host:443/wsman', 'http://resource_uri',
            filter_query='DROP TABLE users', filter_dialect='cql').build()
        payload_obj = lxml.objectify.fromstring(payload)

        self.assertEqual(lxml.etree.tostring(expected_payload_obj),
                         lxml.etree.tostring(payload_obj))

    def test_build_enum_with_invalid_filter_dialect(self):
        invalid_dialect = 'foo'
        self.assertRaises(exceptions.WSManInvalidFilterDialect,
                          dracclient.wsman._EnumeratePayload,
                          'http://host:443/wsman', 'http://resource_uri',
                          filter_query='DROP TABLE users',
                          filter_dialect=invalid_dialect)

    @mock.patch.object(uuid, 'uuid4', autospec=True)
    def test_build_pull(self, mock_uuid):
        expected_payload = """<?xml version="1.0" ?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
            xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <wsa:To s:mustUnderstand="true">http://host:443/wsman</wsa:To>
        <wsman:ResourceURI s:mustUnderstand="true">http://resource_uri</wsman:ResourceURI>
        <wsa:MessageID s:mustUnderstand="true">uuid:1234-12</wsa:MessageID>
        <wsa:ReplyTo>
            <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
        </wsa:ReplyTo>
        <wsa:Action s:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/09/enumeration/Pull</wsa:Action>
    </s:Header>
    <s:Body>
        <wsen:Pull xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration">
            <wsen:EnumerationContext>context-uuid</wsen:EnumerationContext>
            <wsman:MaxElements>100</wsman:MaxElements>
        </wsen:Pull>
    </s:Body>
</s:Envelope>
"""  # noqa
        expected_payload_obj = lxml.objectify.fromstring(expected_payload)

        mock_uuid.return_value = '1234-12'
        payload = dracclient.wsman._PullPayload('http://host:443/wsman',
                                                'http://resource_uri',
                                                'context-uuid').build()
        payload_obj = lxml.objectify.fromstring(payload)

        self.assertEqual(lxml.etree.tostring(expected_payload_obj),
                         lxml.etree.tostring(payload_obj))

    @mock.patch.object(uuid, 'uuid4', autospec=True)
    def test_build_invoke(self, mock_uuid):
        expected_payload = """<?xml version="1.0" ?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
            xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <wsa:To s:mustUnderstand="true">http://host:443/wsman</wsa:To>
        <wsman:ResourceURI s:mustUnderstand="true">http://resource_uri</wsman:ResourceURI>
        <wsa:MessageID s:mustUnderstand="true">uuid:1234-12</wsa:MessageID>
        <wsa:ReplyTo>
            <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
        </wsa:ReplyTo>
        <wsa:Action s:mustUnderstand="true">http://resource_uri/method</wsa:Action>
        <wsman:SelectorSet>
            <wsman:Selector Name="selector">foo</wsman:Selector>
        </wsman:SelectorSet>
    </s:Header>
    <s:Body>
        <ns0:method_INPUT xmlns:ns0="http://resource_uri">
            <ns0:property>bar</ns0:property>
        </ns0:method_INPUT>
    </s:Body>
</s:Envelope>
"""  # noqa
        expected_payload_obj = lxml.objectify.fromstring(expected_payload)

        mock_uuid.return_value = '1234-12'
        payload = dracclient.wsman._InvokePayload(
            'http://host:443/wsman', 'http://resource_uri', 'method',
            {'selector': 'foo'}, {'property': 'bar'}).build()
        payload_obj = lxml.objectify.fromstring(payload)

        self.assertEqual(lxml.etree.tostring(expected_payload_obj),
                         lxml.etree.tostring(payload_obj))

    @mock.patch.object(uuid, 'uuid4', autospec=True)
    def test_build_invoke_with_list_in_properties(self, mock_uuid):
        expected_payload = """<?xml version="1.0" ?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
            xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd">
    <s:Header>
        <wsa:To s:mustUnderstand="true">http://host:443/wsman</wsa:To>
        <wsman:ResourceURI s:mustUnderstand="true">http://resource_uri</wsman:ResourceURI>
        <wsa:MessageID s:mustUnderstand="true">uuid:1234-12</wsa:MessageID>
        <wsa:ReplyTo>
            <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
        </wsa:ReplyTo>
        <wsa:Action s:mustUnderstand="true">http://resource_uri/method</wsa:Action>
        <wsman:SelectorSet>
            <wsman:Selector Name="selector">foo</wsman:Selector>
        </wsman:SelectorSet>
    </s:Header>
    <s:Body>
        <ns0:method_INPUT xmlns:ns0="http://resource_uri">
            <ns0:property>foo</ns0:property>
            <ns0:property>bar</ns0:property>
            <ns0:property>baz</ns0:property>
        </ns0:method_INPUT>
    </s:Body>
</s:Envelope>
"""  # noqa
        expected_payload_obj = lxml.objectify.fromstring(expected_payload)

        mock_uuid.return_value = '1234-12'
        payload = dracclient.wsman._InvokePayload(
            'http://host:443/wsman', 'http://resource_uri', 'method',
            {'selector': 'foo'}, {'property': ['foo', 'bar', 'baz']}).build()
        payload_obj = lxml.objectify.fromstring(payload)

        self.assertEqual(lxml.etree.tostring(expected_payload_obj),
                         lxml.etree.tostring(payload_obj))
