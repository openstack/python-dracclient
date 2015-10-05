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

from dracclient.resources import uris
from dracclient import utils


class LifecycleControllerManagement(object):

    def __init__(self, client):
        """Creates LifecycleControllerManagement object

        :param client: an instance of WSManClient
        """
        self.client = client

    def get_version(self):
        """Returns the Lifecycle controller version

        :returns: Lifecycle controller version as a tuple of integers
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        filter_query = ('select LifecycleControllerVersion '
                        'from DCIM_SystemView')
        doc = self.client.enumerate(uris.DCIM_SystemView,
                                    filter_query=filter_query)
        lc_version_str = utils.find_xml(doc, 'LifecycleControllerVersion',
                                        uris.DCIM_SystemView).text

        return tuple(map(int, (lc_version_str.split('.'))))
