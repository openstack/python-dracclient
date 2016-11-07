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

import re

from lxml import etree

from dracclient import exceptions
from dracclient.resources import uris
from dracclient.tests import base
from dracclient.tests import utils as test_utils
from dracclient import utils


class UtilsTestCase(base.BaseTest):

    def setUp(self):
        super(UtilsTestCase, self).setUp()

    def test_get_wsman_resource_attr(self):
        doc = etree.fromstring(
            test_utils.InventoryEnumerations[uris.DCIM_CPUView]['ok'])
        cpus = utils.find_xml(doc, 'DCIM_CPUView', uris.DCIM_CPUView,
                              find_all=True)

        val = utils.get_wsman_resource_attr(
            cpus[0], uris.DCIM_CPUView, 'HyperThreadingEnabled',
            allow_missing=False)

        self.assertEqual('1', val)

    def test_get_wsman_resource_attr_missing_attr(self):
        expected_message = ("Could not find attribute 'HyperThreadingEnabled'")
        doc = etree.fromstring(
            test_utils.InventoryEnumerations[
                uris.DCIM_CPUView]['missing_flags'])
        cpus = utils.find_xml(doc, 'DCIM_CPUView', uris.DCIM_CPUView,
                              find_all=True)

        self.assertRaisesRegexp(
            AttributeError, re.escape(expected_message),
            utils.get_wsman_resource_attr, cpus[0], uris.DCIM_CPUView,
            'HyperThreadingEnabled', allow_missing=False)

    def test_get_wsman_resource_attr_missing_attr_allowed(self):
        doc = etree.fromstring(
            test_utils.InventoryEnumerations[
                uris.DCIM_CPUView]['missing_flags'])
        cpus = utils.find_xml(doc, 'DCIM_CPUView', uris.DCIM_CPUView,
                              find_all=True)

        val = utils.get_wsman_resource_attr(
            cpus[0], uris.DCIM_CPUView, 'HyperThreadingEnabled',
            allow_missing=True)

        self.assertIsNone(val)

    def test_get_wsman_resource_attr_missing_text(self):
        expected_message = ("Attribute 'HyperThreadingEnabled' is not nullable"
                            ", but no value received")
        doc = etree.fromstring(
            test_utils.InventoryEnumerations[
                uris.DCIM_CPUView]['empty_flag'])
        cpus = utils.find_xml(doc, 'DCIM_CPUView', uris.DCIM_CPUView,
                              find_all=True)

        self.assertRaisesRegexp(
            exceptions.DRACEmptyResponseField, re.escape(expected_message),
            utils.get_wsman_resource_attr, cpus[0], uris.DCIM_CPUView,
            'HyperThreadingEnabled', allow_missing=False)
