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

import logging
import uuid

from lxml import etree as ElementTree
import requests
import requests.exceptions

from dracclient import exceptions

LOG = logging.getLogger(__name__)

NS_SOAP_ENV = 'http://www.w3.org/2003/05/soap-envelope'
NS_WS_ADDR = 'http://schemas.xmlsoap.org/ws/2004/08/addressing'
NS_WS_ADDR_ANONYM_ROLE = ('http://schemas.xmlsoap.org/ws/2004/08/addressing/'
                          'role/anonymous')
NS_WSMAN = 'http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd'
NS_WSMAN_ENUM = 'http://schemas.xmlsoap.org/ws/2004/09/enumeration'

NS_MAP = {'s': NS_SOAP_ENV,
          'wsa': NS_WS_ADDR,
          'wsman': NS_WSMAN}

FILTER_DIALECT_MAP = {'cql': 'http://schemas.dmtf.org/wbem/cql/1/dsp0202.pdf',
                      'wql': 'http://schemas.microsoft.com/wbem/wsman/1/WQL'}


class Client(object):
    """Simple client for talking over WSMan protocol."""

    def __init__(self, host, username, password, port=443, path='/wsman',
                 protocol='https'):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.path = path
        self.protocol = protocol
        self.endpoint = ('%(protocol)s://%(host)s:%(port)s%(path)s' % {
            'protocol': self.protocol,
            'host': self.host,
            'port': self.port,
            'path': self.path})

    def _do_request(self, payload):
        payload = payload.build()
        LOG.debug('Sending request to %(endpoint)s: %(payload)s',
                  {'endpoint': self.endpoint, 'payload': payload})
        try:
            resp = requests.post(
                self.endpoint,
                auth=requests.auth.HTTPBasicAuth(self.username, self.password),
                data=payload,
                # TODO(ifarkas): enable cert verification
                verify=False)
        except requests.exceptions.RequestException:
            LOG.exception('Request failed')
            raise exceptions.WSManRequestFailure()

        LOG.debug('Received response from %(endpoint)s: %(payload)s',
                  {'endpoint': self.endpoint, 'payload': resp.content})
        if not resp.ok:
            raise exceptions.WSManInvalidResponse(
                status_code=resp.status_code,
                reason=resp.reason)
        else:
            return resp

    def enumerate(self, resource_uri, optimization=True, max_elems=100,
                  auto_pull=True, filter_query=None, filter_dialect='cql'):
        """Executes enumerate operation over WSMan.

        :param resource_uri: URI of resource to enumerate.
        :param optimization: flag to enable enumeration optimization. If
                             disabled, the enumeration returns only an
                             enumeration context.
        :param max_elems: maximum number of elements returned by the operation.
        :param auto_pull: flag to enable automatic pull on the enumeration
                          context, merging the items returned.
        :param filter_query: filter query string.
        :param filter_dialect: filter dialect. Valid options are: 'cql' and
                               'wql'.
        :returns: an lxml.etree.Element object of the response received.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        """

        payload = _EnumeratePayload(self.endpoint, resource_uri,
                                    optimization, max_elems,
                                    filter_query, filter_dialect)

        resp = self._do_request(payload)
        resp_xml = ElementTree.fromstring(resp.content)

        if auto_pull:
            # The first response returns "<wsman:Items>"
            find_items_wsman_query = './/{%s}Items' % NS_WSMAN

            # Successive pulls return "<wsen:Items>"
            find_items_enum_query = './/{%s}Items' % NS_WSMAN_ENUM

            full_resp_xml = resp_xml
            items_xml = full_resp_xml.find(find_items_wsman_query)

            context = self._enum_context(full_resp_xml)
            while context is not None:
                resp_xml = self.pull(resource_uri, context, max_elems)
                context = self._enum_context(resp_xml)

                # Merge in next batch of enumeration items
                for item in resp_xml.find(find_items_enum_query):
                    items_xml.append(item)

            # remove enumeration context because items are already merged
            enum_context_elem = full_resp_xml.find('.//{%s}EnumerationContext'
                                                   % NS_WSMAN_ENUM)
            if enum_context_elem is not None:
                enum_context_elem.getparent().remove(enum_context_elem)

            return full_resp_xml
        else:
            return resp_xml

    def pull(self, resource_uri, context, max_elems=100):
        """Executes pull operation over WSMan.

        :param resource_uri: URI of resource to pull
        :param context: enumeration context
        :param max_elems: maximum number of elements returned by the operation
        :returns: an lxml.etree.Element object of the response received
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        """

        payload = _PullPayload(self.endpoint, resource_uri, context,
                               max_elems)
        resp = self._do_request(payload)
        resp_xml = ElementTree.fromstring(resp.content)

        return resp_xml

    def invoke(self, resource_uri, method, selectors, properties):
        """Executes invoke operation over WSMan.

        :param resource_uri: URI of resource to invoke
        :param method: name of the method to invoke
        :param selector: dict of selectors
        :param properties: dict of properties
        :returns: an lxml.etree.Element object of the response received.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        """

        payload = _InvokePayload(self.endpoint, resource_uri, method,
                                 selectors, properties)
        resp = self._do_request(payload)
        resp_xml = ElementTree.fromstring(resp.content)

        return resp_xml

    def _enum_context(self, resp):
        context_elem = resp.find('.//{%s}EnumerationContext' % NS_WSMAN_ENUM)
        if context_elem is not None:
            return context_elem.text


class _Payload(object):
    """Payload generation for WSMan requests."""

    def build(self):
        request = self._create_envelope()
        self._add_header(request)
        self._add_body(request)

        return ElementTree.tostring(request)

    def _create_envelope(self):
        return ElementTree.Element('{%s}Envelope' % NS_SOAP_ENV, nsmap=NS_MAP)

    def _add_header(self, envelope):
        header = ElementTree.SubElement(envelope, '{%s}Header' % NS_SOAP_ENV)

        qn_must_understand = ElementTree.QName(NS_SOAP_ENV, 'mustUnderstand')

        to_elem = ElementTree.SubElement(header, '{%s}To' % NS_WS_ADDR)
        to_elem.set(qn_must_understand, 'true')
        to_elem.text = self.endpoint

        resource_elem = ElementTree.SubElement(header,
                                               '{%s}ResourceURI' % NS_WSMAN)
        resource_elem.set(qn_must_understand, 'true')
        resource_elem.text = self.resource_uri

        msg_id_elem = ElementTree.SubElement(header,
                                             '{%s}MessageID' % NS_WS_ADDR)
        msg_id_elem.set(qn_must_understand, 'true')
        msg_id_elem.text = 'uuid:%s' % uuid.uuid4()

        reply_to_elem = ElementTree.SubElement(header,
                                               '{%s}ReplyTo' % NS_WS_ADDR)
        reply_to_addr_elem = ElementTree.SubElement(reply_to_elem,
                                                    '{%s}Address' % NS_WS_ADDR)
        reply_to_addr_elem.text = NS_WS_ADDR_ANONYM_ROLE

        return header

    def _add_body(self, envelope):
        return ElementTree.SubElement(envelope, '{%s}Body' % NS_SOAP_ENV)


class _EnumeratePayload(_Payload):
    """Payload generation for WSMan enumerate operation."""

    def __init__(self, endpoint, resource_uri, optimization=True,
                 max_elems=100, filter_query=None, filter_dialect=None):
        self.endpoint = endpoint
        self.resource_uri = resource_uri
        self.filter_dialect = None
        self.filter_query = None
        self.optimization = optimization
        self.max_elems = max_elems

        if filter_query is not None:
            try:
                self.filter_dialect = FILTER_DIALECT_MAP[filter_dialect]
            except KeyError:
                valid_opts = ', '.join(FILTER_DIALECT_MAP)
                raise exceptions.WSManInvalidFilterDialect(
                    invalid_filter=filter_dialect, supported=valid_opts)

            self.filter_query = filter_query

    def _add_header(self, envelope):
        header = super(_EnumeratePayload, self)._add_header(envelope)

        action_elem = ElementTree.SubElement(header, '{%s}Action' % NS_WS_ADDR)
        action_elem.set('{%s}mustUnderstand' % NS_SOAP_ENV, 'true')
        action_elem.text = NS_WSMAN_ENUM + '/Enumerate'

        return header

    def _add_body(self, envelope):
        body = super(_EnumeratePayload, self)._add_body(envelope)

        enum_elem = ElementTree.SubElement(body,
                                           '{%s}Enumerate' % NS_WSMAN_ENUM,
                                           nsmap={'wsen': NS_WSMAN_ENUM})

        if self.filter_query is not None:
            self._add_filter(enum_elem)

        if self.optimization:
            self._add_enum_optimization(enum_elem)

        return body

    def _add_enum_optimization(self, enum_elem):
        ElementTree.SubElement(enum_elem,
                               '{%s}OptimizeEnumeration' % NS_WSMAN)

        max_elem_elem = ElementTree.SubElement(enum_elem,
                                               '{%s}MaxElements' % NS_WSMAN)
        max_elem_elem.text = str(self.max_elems)

    def _add_filter(self, enum_elem):
        filter_elem = ElementTree.SubElement(enum_elem,
                                             '{%s}Filter' % NS_WSMAN)
        filter_elem.set('Dialect', self.filter_dialect)
        filter_elem.text = self.filter_query


class _PullPayload(_Payload):
    """Payload generation for WSMan pull operation."""

    def __init__(self, endpoint, resource_uri, context, max_elems=100):
        self.endpoint = endpoint
        self.resource_uri = resource_uri
        self.context = context
        self.max_elems = max_elems

    def _add_header(self, envelope):
        header = super(_PullPayload, self)._add_header(envelope)

        action_elem = ElementTree.SubElement(header, '{%s}Action' % NS_WS_ADDR)
        action_elem.set('{%s}mustUnderstand' % NS_SOAP_ENV, 'true')
        action_elem.text = NS_WSMAN_ENUM + '/Pull'

        return header

    def _add_body(self, envelope):
        body = super(_PullPayload, self)._add_body(envelope)

        pull_elem = ElementTree.SubElement(body,
                                           '{%s}Pull' % NS_WSMAN_ENUM,
                                           nsmap={'wsen': NS_WSMAN_ENUM})

        enum_context_elem = ElementTree.SubElement(
            pull_elem, '{%s}EnumerationContext' % NS_WSMAN_ENUM)
        enum_context_elem.text = self.context

        self._add_enum_optimization(pull_elem)

        return body

    def _add_enum_optimization(self, pull_elem):
        max_elem_elem = ElementTree.SubElement(pull_elem,
                                               '{%s}MaxElements' % NS_WSMAN)
        max_elem_elem.text = str(self.max_elems)


class _InvokePayload(_Payload):
    """Payload generation for WSMan invoke operation."""

    def __init__(self, endpoint, resource_uri, method, selectors=None,
                 properties=None):
        self.endpoint = endpoint
        self.resource_uri = resource_uri
        self.method = method
        self.selectors = selectors
        self.properties = properties

    def _add_header(self, envelope):
        header = super(_InvokePayload, self)._add_header(envelope)

        action_elem = ElementTree.SubElement(header, '{%s}Action' % NS_WS_ADDR)
        action_elem.set('{%s}mustUnderstand' % NS_SOAP_ENV, 'true')
        action_elem.text = ('%(resource_uri)s/%(method)s' %
                            {'resource_uri': self.resource_uri,
                             'method': self.method})

        self._add_selectors(header)

        return header

    def _add_body(self, envelope):
        body = super(_InvokePayload, self)._add_body(envelope)
        self._add_properties(body)

        return body

    def _add_selectors(self, header):
        selector_set_elem = ElementTree.SubElement(
            header, '{%s}SelectorSet' % NS_WSMAN)

        for (name, value) in self.selectors.items():
            selector_elem = ElementTree.SubElement(selector_set_elem,
                                                   '{%s}Selector' % NS_WSMAN)
            selector_elem.set('Name', name)
            selector_elem.text = value

    def _add_properties(self, body):
        method_elem = ElementTree.SubElement(
            body,
            ('{%(resource_uri)s}%(method)s_INPUT' %
                {'resource_uri': self.resource_uri,
                 'method': self.method}))

        for (name, value) in self.properties.items():
            if not isinstance(value, list):
                value = [value]

            for item in value:
                property_elem = ElementTree.SubElement(
                    method_elem,
                    ('{%(resource_uri)s}%(name)s' %
                     {'resource_uri': self.resource_uri,
                      'name': name}))
                property_elem.text = item
