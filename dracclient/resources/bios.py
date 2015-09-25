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

from dracclient import constants
from dracclient import exceptions
from dracclient.resources import uris
from dracclient import utils

POWER_STATES = {
    '2': constants.POWER_ON,
    '3': constants.POWER_OFF,
    '11': constants.REBOOT,
}

REVERSE_POWER_STATES = dict((v, k) for (k, v) in POWER_STATES.items())


class PowerManagement(object):

    def __init__(self, client):
        """Creates PowerManagement object

        :param client: an instance of WSManClient
        """
        self.client = client

    def get_power_state(self):
        """Returns the current power state of the node

        :returns: power state of the node, one of 'POWER_ON', 'POWER_OFF' or
                  'REBOOT'
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        filter_query = ('select EnabledState from '
                        'DCIM_ComputerSystem where Name="srv:system"')
        doc = self.client.enumerate(uris.DCIM_ComputerSystem,
                                    filter_query=filter_query)
        enabled_state = utils.find_xml(doc, 'EnabledState',
                                       uris.DCIM_ComputerSystem)

        return POWER_STATES[enabled_state.text]

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

        try:
            drac_requested_state = REVERSE_POWER_STATES[target_state]
        except KeyError:
            msg = ("'%(target_state)s' is not supported. "
                   "Supported power states: %(supported_power_states)r") % {
                       'target_state': target_state,
                       'supported_power_states': list(REVERSE_POWER_STATES)}
            raise exceptions.InvalidParameterValue(reason=msg)

        selectors = {'CreationClassName': 'DCIM_ComputerSystem',
                     'Name': 'srv:system'}
        properties = {'RequestedState': drac_requested_state}

        self.client.invoke(uris.DCIM_ComputerSystem, 'RequestStateChange',
                           selectors, properties)
