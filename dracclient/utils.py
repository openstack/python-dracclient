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

from dracclient import constants
import logging

from dracclient import exceptions
from dracclient import wsman

LOG = logging.getLogger(__name__)

NS_XMLSchema_Instance = 'http://www.w3.org/2001/XMLSchema-instance'

# ReturnValue constants
RET_SUCCESS = '0'
RET_ERROR = '2'
RET_CREATED = '4096'

REBOOT_REQUIRED = {
    'yes': constants.RebootRequired.true,
    'no': constants.RebootRequired.false,
    'optional': constants.RebootRequired.optional
}


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


def build_return_dict(doc, resource_uri,
                      is_commit_required_value=None,
                      is_reboot_required_value=None):
    """Builds a dictionary to be returned

       Build a dictionary to be returned from WSMAN operations that are not
       read-only.

    :param doc: the element tree object.
    :param resource_uri: the resource URI of the namespace.
    :param is_commit_required_value: The value to be returned for
           is_commit_required, or None if the value should be determined
           from the doc.
    :param is_reboot_required_value: The value to be returned for
           is_reboot_required, or None if the value should be determined
           from the doc.
    :returns: a dictionary containing:
             - is_commit_required: indicates if a commit is required.
             - is_reboot_required: indicates if a reboot is required.
    """

    if is_reboot_required_value is not None and \
            is_reboot_required_value not in constants.RebootRequired.all():
        msg = ("is_reboot_required_value must be a member of the "
               "RebootRequired enumeration or None.  The passed value was "
               "%(is_reboot_required_value)s" % {
                   'is_reboot_required_value': is_reboot_required_value})
        raise exceptions.InvalidParameterValue(reason=msg)

    result = {}
    if is_commit_required_value is None:
        is_commit_required_value = is_commit_required(doc, resource_uri)

    result['is_commit_required'] = is_commit_required_value

    if is_reboot_required_value is None:
        is_reboot_required_value = reboot_required(doc, resource_uri)

    result['is_reboot_required'] = is_reboot_required_value

    return result


def is_commit_required(doc, resource_uri):
    """Check the response document if commit is required.

    If SetResult contains "pending" in the response then a commit is required.

    :param doc: the element tree object.
    :param resource_uri: the resource URI of the namespace.
    :returns: a boolean value indicating commit is required or not.
    """

    commit_required = find_xml(doc, 'SetResult', resource_uri)
    return "pendingvalue" in commit_required.text.lower()


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


def reboot_required(doc, resource_uri):
    """Check the response document if reboot is requested.

    RebootRequired attribute in the response indicates whether node needs to
    be rebooted, so that the pending changes can be committed.

    :param doc: the element tree object.
    :param resource_uri: the resource URI of the namespace.
    :returns: True if reboot is required, False if it is not, and the string
              "optional" if reboot is optional.
    """

    reboot_required_value = find_xml(doc, 'RebootRequired', resource_uri)
    return REBOOT_REQUIRED[reboot_required_value.text.lower()]


def validate_integer_value(value, attr_name, error_msgs):
    """Validate integer value"""

    if value is None:
        error_msgs.append("'%s' is not supplied" % attr_name)
        return

    try:
        int(value)
    except ValueError:
        error_msgs.append("'%s' is not an integer value" % attr_name)


def list_settings(client, namespaces, by_name=True, fqdd_filter=None,
                  name_formatter=None):
    """List the configuration settings

    :param client: an instance of WSManClient.
    :param namespaces: a list of URI/class pairs to retrieve.
    :param by_name: controls whether returned dictionary uses
                    attribute name or instance_id as key.
    :param fqdd_filter: An FQDD used to filter the instances.  Note that
                        this is only used when by_name is True.
    :param name_formatter: a method used to format the keys in the
                           returned dictionary.  By default,
                           attribute.name will be used.
    :returns: a dictionary with the settings using name or instance_id as
              the key.
    :raises: WSManRequestFailure on request failures
    :raises: WSManInvalidResponse when receiving invalid response
    :raises: DRACOperationFailed on error reported back by the DRAC
             interface
    """

    result = {}
    for (namespace, attr_cls) in namespaces:
        attribs = _get_config(client, namespace, attr_cls, by_name,
                              fqdd_filter, name_formatter)
        if not set(result).isdisjoint(set(attribs)):
            raise exceptions.DRACOperationFailed(
                drac_messages=('Colliding attributes %r' % (
                    set(result) & set(attribs))))
        result.update(attribs)
    return result


def _get_config(client, resource, attr_cls, by_name, fqdd_filter,
                name_formatter):
    result = {}

    doc = client.enumerate(resource)
    items = doc.find('.//{%s}Items' % wsman.NS_WSMAN)

    for item in items:
        attribute = attr_cls.parse(item)
        if by_name:
            # Filter out all instances without a matching FQDD
            if fqdd_filter is None or fqdd_filter == attribute.fqdd:
                if name_formatter is None:
                    name = attribute.name
                else:
                    name = name_formatter(attribute)

                result[name] = attribute
        else:
            result[attribute.instance_id] = attribute

    return result


def set_settings(settings_type,
                 client,
                 namespaces,
                 new_settings,
                 resource_uri,
                 cim_creation_class_name,
                 cim_name,
                 target,
                 name_formatter=None):
    """Generically handles setting various types of settings on the iDRAC

    This method pulls the current list of settings from the iDRAC then compares
    that list against the passed new settings to determine if there are any
    errors.  If no errors exist then the settings are sent to the iDRAC using
    the passed resource, target, etc.

    :param settings_type: a string indicating the settings type
    :param client: an instance of WSManClient
    :param namespaces: a list of URI/class pairs to retrieve.
    :param new_settings: a dictionary containing the proposed values, with
                         each key being the name of attribute and the
                         value being the proposed value.
    :param resource_uri: URI of resource to invoke
    :param cim_creation_class_name: creation class name of the CIM object
    :param cim_name: name of the CIM object
    :param target: target device
    :param name_formatter: a method used to format the keys in the
                           returned dictionary.  By default,
                           attribute.name will be used.
    :returns: a dictionary containing:
             - The is_commit_required key with a boolean value indicating
               whether a config job must be created for the values to be
               applied.
             - The is_reboot_required key with a RebootRequired enumerated
               value indicating whether the server must be rebooted for the
               values to be applied.  Possible values are true and false.
    :raises: WSManRequestFailure on request failures
    :raises: WSManInvalidResponse when receiving invalid response
    :raises: DRACOperationFailed on new settings with invalid values or
             attempting to set read-only settings or when an error is reported
             back by the iDRAC interface
    :raises: DRACUnexpectedReturnValue on return value mismatch
    :raises: InvalidParameterValue on invalid new setting
    """

    current_settings = list_settings(client, namespaces, by_name=True,
                                     name_formatter=name_formatter)

    unknown_keys = set(new_settings) - set(current_settings)
    if unknown_keys:
        msg = ('Unknown %(settings_type)s attributes found: %(unknown_keys)r' %
               {'settings_type': settings_type, 'unknown_keys': unknown_keys})
        raise exceptions.InvalidParameterValue(reason=msg)

    read_only_keys = []
    unchanged_attribs = []
    invalid_attribs_msgs = []
    attrib_names = []
    candidates = set(new_settings)

    for attr in candidates:
        if str(new_settings[attr]) == str(
                current_settings[attr].current_value):
            unchanged_attribs.append(attr)
        elif current_settings[attr].read_only:
            read_only_keys.append(attr)
        else:
            validation_msg = current_settings[attr].validate(
                new_settings[attr])
            if not validation_msg:
                attrib_names.append(attr)
            else:
                invalid_attribs_msgs.append(validation_msg)

    if unchanged_attribs:
        LOG.debug('Ignoring unchanged %(settings_type)s attributes: '
                  '%(unchanged_attribs)r' %
                  {'settings_type': settings_type,
                   'unchanged_attribs': unchanged_attribs})

    if invalid_attribs_msgs or read_only_keys:
        if read_only_keys:
            read_only_msg = ['Cannot set read-only %(settings_type)s '
                             'attributes: %(read_only_keys)r.' %
                             {'settings_type': settings_type,
                              'read_only_keys': read_only_keys}]
        else:
            read_only_msg = []

        drac_messages = '\n'.join(invalid_attribs_msgs + read_only_msg)
        raise exceptions.DRACOperationFailed(
            drac_messages=drac_messages)

    if not attrib_names:
        return build_return_dict(
            None,
            resource_uri,
            is_commit_required_value=False,
            is_reboot_required_value=constants.RebootRequired.false)

    selectors = {'CreationClassName': cim_creation_class_name,
                 'Name': cim_name,
                 'SystemCreationClassName': 'DCIM_ComputerSystem',
                 'SystemName': 'DCIM:ComputerSystem'}
    properties = {'Target': target,
                  'AttributeName': attrib_names,
                  'AttributeValue': [new_settings[attr] for attr
                                     in attrib_names]}
    doc = client.invoke(resource_uri, 'SetAttributes',
                        selectors, properties)

    return build_return_dict(doc, resource_uri)
