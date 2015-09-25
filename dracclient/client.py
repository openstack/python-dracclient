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

"""
Wrapper for pywsman.Client
"""

import logging

from dracclient import exceptions
from dracclient.resources import bios
from dracclient import utils
from dracclient import wsman

LOG = logging.getLogger(__name__)


class DRACClient(object):
    """Client for managing DRAC nodes"""

    def __init__(self, host, username, password, port=443, path='/wsman',
                 protocol='https'):
        """Creates client object

        :param host: hostname or IP of the DRAC interface
        :param username: username for accessing the DRAC interface
        :param password: password for accessing the DRAC interface
        :param port: port for accessing the DRAC interface
        :param path: path for accessing the DRAC interface
        :param protocol: protocol for accessing the DRAC interface
        """
        self.client = WSManClient(host, username, password, port, path,
                                  protocol)
        self._power_mgmt = bios.PowerManagement(self.client)

    def get_power_state(self):
        """Returns the current power state of the node

        :returns: power state of the node, one of 'POWER_ON', 'POWER_OFF' or
                  'REBOOT'
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._power_mgmt.get_power_state()

    def set_power_state(self, target_state):
        """Turns the server power on/off or do a reboot

        :param target_state: target power state. Valid options are: 'POWER_ON',
                             'POWER_OFF' and 'REBOOT'.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        :raises: InvalidParameterValue on invalid target power state
        """
        self._power_mgmt.set_power_state(target_state)


class WSManClient(wsman.Client):
    """Wrapper for wsman.Client with return value checking"""

    def invoke(self, resource_uri, method, selectors=None, properties=None,
               expected_return_value=None):
        """Invokes a remote WS-Man method

        :param resource_uri: URI of the resource
        :param method: name of the method to invoke
        :param selectors: dictionary of selectors
        :param properties: dictionary of properties
        :param expected_return_value: expected return value reported back by
            the DRAC card. For return value codes check the profile
            documentation of the resource used in the method call. If not set,
            return value checking is skipped.
        :returns: an lxml.etree.Element object of the response received
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        if selectors is None:
            selectors = {}

        if properties is None:
            properties = {}

        resp = super(WSManClient, self).invoke(resource_uri, method, selectors,
                                               properties)

        return_value = utils.find_xml(resp, 'ReturnValue', resource_uri).text
        if return_value == utils.RET_ERROR:
            message_elems = utils.find_xml(resp, 'Message', resource_uri, True)
            messages = [message_elem.text for message_elem in message_elems]
            raise exceptions.DRACOperationFailed(drac_messages=messages)

        if (expected_return_value is not None and
                return_value != expected_return_value):
            raise exceptions.DRACUnexpectedReturnValue(
                expected_return_value=expected_return_value,
                actual_return_value=return_value)

        return resp
