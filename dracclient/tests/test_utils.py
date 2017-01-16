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

    def test__is_attr_non_nil_True(self):
        doc = etree.fromstring(
            test_utils.RAIDEnumerations[
                uris.DCIM_ControllerView]['ok'])
        controllers = utils.find_xml(doc, 'DCIM_ControllerView',
                                     uris.DCIM_ControllerView, find_all=True)
        version = utils.find_xml(controllers[0], 'Bus',
                                 uris.DCIM_ControllerView)

        self.assertTrue(utils._is_attr_non_nil(version))

    def test__is_attr_non_nil_False(self):
        doc = etree.fromstring(
            test_utils.RAIDEnumerations[
                uris.DCIM_ControllerView]['ok'])
        controllers = utils.find_xml(doc, 'DCIM_ControllerView',
                                     uris.DCIM_ControllerView, find_all=True)
        version = utils.find_xml(controllers[0], 'DriverVersion',
                                 uris.DCIM_ControllerView)

        self.assertFalse(utils._is_attr_non_nil(version))

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
        expected_message = ("Attribute 'HyperThreadingEnabled' is missing "
                            "from the response")
        doc = etree.fromstring(
            test_utils.InventoryEnumerations[
                uris.DCIM_CPUView]['missing_flags'])
        cpus = utils.find_xml(doc, 'DCIM_CPUView', uris.DCIM_CPUView,
                              find_all=True)

        self.assertRaisesRegexp(
            exceptions.DRACMissingResponseField, re.escape(expected_message),
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

    def test_get_wsman_resource_attr_missing_text_allowed(self):
        doc = etree.fromstring(
            test_utils.RAIDEnumerations[
                uris.DCIM_ControllerView]['ok'])
        controllers = utils.find_xml(doc, 'DCIM_ControllerView',
                                     uris.DCIM_ControllerView, find_all=True)

        result = utils.get_wsman_resource_attr(
            controllers[0], uris.DCIM_ControllerView, 'DriverVersion',
            allow_missing=False, nullable=True)
        self.assertIsNone(result)

    def test_get_all_wsman_resource_attrs(self):
        doc = etree.fromstring(
            test_utils.RAIDEnumerations[uris.DCIM_VirtualDiskView]['ok'])
        vdisks = utils.find_xml(doc, 'DCIM_VirtualDiskView',
                                uris.DCIM_VirtualDiskView, find_all=True)

        vals = utils.get_all_wsman_resource_attrs(
            vdisks[0], uris.DCIM_VirtualDiskView, 'PhysicalDiskIDs')

        expected_pdisks = [
            'Disk.Bay.0:Enclosure.Internal.0-1:RAID.Integrated.1-1',
            'Disk.Bay.1:Enclosure.Internal.0-1:RAID.Integrated.1-1'
        ]
        self.assertListEqual(expected_pdisks, vals)

    def test_get_all_wsman_resource_attrs_missing_attr_allowed(self):
        doc = etree.fromstring(
            test_utils.InventoryEnumerations[
                uris.DCIM_CPUView]['missing_flags'])
        cpus = utils.find_xml(doc, 'DCIM_CPUView', uris.DCIM_CPUView,
                              find_all=True)

        vals = utils.get_all_wsman_resource_attrs(
            cpus[0], uris.DCIM_CPUView, 'HyperThreadingEnabled')

        self.assertListEqual([], vals)

    def test_get_all_wsman_resource_attrs_missing_text(self):
        expected_message = ("Attribute 'HyperThreadingEnabled' is not nullable"
                            ", but no value received")
        doc = etree.fromstring(
            test_utils.InventoryEnumerations[
                uris.DCIM_CPUView]['empty_flag'])
        cpus = utils.find_xml(doc, 'DCIM_CPUView', uris.DCIM_CPUView,
                              find_all=True)

        self.assertRaisesRegexp(
            exceptions.DRACEmptyResponseField, re.escape(expected_message),
            utils.get_all_wsman_resource_attrs, cpus[0], uris.DCIM_CPUView,
            'HyperThreadingEnabled')

    def test_get_all_wsman_resource_attrs_missing_text_allowed(self):
        doc = etree.fromstring(
            test_utils.RAIDEnumerations[
                uris.DCIM_ControllerView]['ok'])
        controllers = utils.find_xml(doc, 'DCIM_ControllerView',
                                     uris.DCIM_ControllerView, find_all=True)

        result = utils.get_all_wsman_resource_attrs(
            controllers[0], uris.DCIM_ControllerView, 'DriverVersion',
            nullable=True)
        self.assertEqual(result, [])
