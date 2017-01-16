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
Common functionalities shared between different DRAC modules.
"""

from dracclient import exceptions

NS_XMLSchema_Instance = 'http://www.w3.org/2001/XMLSchema-instance'

# ReturnValue constants
RET_SUCCESS = '0'
RET_ERROR = '2'
RET_CREATED = '4096'


def find_xml(doc, item, namespace, find_all=False):
    """Find the first or all elements in an ElementTree object.

    :param doc: the element tree object.
    :param item: the element name.
    :param namespace: the namespace of the element.
    :param find_all: Boolean value, if True find all elements, if False
                     find only the first one. Defaults to False.
    :returns: if find_all is False the element object will be returned
              if found, None if not found. If find_all is True a list of
              element objects will be returned or an empty list if no
              elements were found.

    """
    query = ('.//{%(namespace)s}%(item)s' % {'namespace': namespace,
                                             'item': item})
    if find_all:
        return doc.findall(query)
    return doc.find(query)


def _is_attr_non_nil(elem):
    """Return whether an element is non-nil.

    :param elem: the element object.
    :returns: whether the element is nil.
    """
    return elem.attrib.get('{%s}nil' % NS_XMLSchema_Instance) != 'true'


def get_wsman_resource_attr(doc, resource_uri, attr_name, nullable=False,
                            allow_missing=False):
    """Find an attribute of a resource in an ElementTree object.

    :param doc: the element tree object.
    :param resource_uri: the resource URI of the namespace.
    :param attr_name: the name of the attribute.
    :param nullable: enables checking if the element contains an
                     XMLSchema-instance namespaced nil attribute that has a
                     value of True. In this case, it will return None.
    :param allow_missing: if set to True, attributes missing from the XML
                          document will return None instead of raising
                          DRACMissingResponseField.
    :raises: DRACMissingResponseField if the attribute is missing from the XML
             doc and allow_missing is False.
    :raises: DRACEmptyResponseField if the attribute is present in the XML doc
             but it has no text and nullable is False.
    :returns: value of the attribute
    """
    item = find_xml(doc, attr_name, resource_uri)

    if item is None:
        if allow_missing:
            return
        else:
            raise exceptions.DRACMissingResponseField(attr=attr_name)

    if not nullable:
        if item.text is None:
            raise exceptions.DRACEmptyResponseField(attr=attr_name)
        return item.text.strip()
    else:
        if _is_attr_non_nil(item):
            return item.text.strip()


def get_all_wsman_resource_attrs(doc, resource_uri, attr_name, nullable=False):
    """Find all instances of an attribute of a resource in an ElementTree.

    :param doc: the element tree object.
    :param resource_uri: the resource URI of the namespace.
    :param attr_name: the name of the attribute.
    :param nullable: enables checking if any of the elements contain an
                     XMLSchema-instance namespaced nil attribute that has a
                     value of True. In this case, these elements will not be
                     returned.
    :raises: DRACEmptyResponseField if any of the attributes in the XML doc
             have no text and nullable is False.
    :returns: a list containing the value of each of the instances of the
              attribute.
    """
    items = find_xml(doc, attr_name, resource_uri, find_all=True)

    if not nullable:
        for item in items:
            if item.text is None:
                raise exceptions.DRACEmptyResponseField(attr=attr_name)
        return [item.text.strip() for item in items]
    else:

        return [item.text.strip() for item in items if _is_attr_non_nil(item)]


def is_reboot_required(doc, resource_uri):
    """Check the response document if reboot is requested.

    RebootRequired attribute in the response indicates whether a config job
    needs to be created and the node needs to be rebooted, so that the
    Lifecycle controller can commit the pending changes.

    :param doc: the element tree object.
    :param resource_uri: the resource URI of the namespace.
    :returns: a boolean value indicating reboot was requested or not.
    """

    reboot_required = find_xml(doc, 'RebootRequired', resource_uri)
    return reboot_required.text.lower() == 'yes'


def validate_integer_value(value, attr_name, error_msgs):
    """Validate integer value"""

    if value is None:
        error_msgs.append("'%s' is not supplied" % attr_name)
        return

    try:
        int(value)
    except ValueError:
        error_msgs.append("'%s' is not an integer value" % attr_name)
