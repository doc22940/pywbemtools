# (C) Copyright 2019 IBM Corp.
# (C) Copyright 2019 Inova Development Inc.
# All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Class to represent the concept and implementation of an association shrub.

A shrub is a view of association relations that gathers and presents all of the
information about a relation. I differs from the associator and reference
commands in that they present the user with just a set of CIM objects or
their names, and not a view of the relations between the components that
make up a CIM association.

It is based on the parameters of the pywbem associators operation.

It builds the information by using the reference and association operations to
gather data from the server and present either a table or tree view of
the relations that link a source instance and the target instances of an
association.
"""


from __future__ import absolute_import, print_function, unicode_literals

from collections import defaultdict
import six
import click


# TODO Could we combine this tree into tree file???
from asciitree import LeftAligned

from pywbem import CIMInstanceName, CIMClassName, \
    CIMFloat, CIMInt, CIMError, CIMDateTime
from pywbem._utils import _to_unicode, _ensure_unicode, _format

from ._common import output_format_is_table, format_table

# Same as in pwbem.cimtypes.py
if six.PY2:
    # pylint: disable=invalid-name,undefined-variable
    _Longint = long  # noqa: F821
else:
    # pylint: disable=invalid-name
    _Longint = int


class AssociationShrub(object):
    """
    This class provides tools for the acquisition and display of an association
    that includes much more information than the DMTF defined operation
    Associatiors.  Using the same input parameters, it allows displaying
    the the components that make up an association as either a table or a
    tree including the reference classes, and roles.
    """
    def __init__(self, context, source_path, Role=None, AssocClass=None,
                 ResultRole=None, ResultClass=None, verbose=None):
        self.source_path = source_path
        # list of all unique hosted_classnames for reference classes.
        # This is list of CIMClassName to insure that we provide host, namespace
        # where necessary
        # self.reference_classnames = []
        self.context = context
        self.conn = context.conn
        self.shrub_dict = {}
        self.role = Role
        self.assoc_class = AssocClass
        self.result_role = ResultRole
        self.result_class = ResultClass
        self.verbose = verbose

        # assoc_classnames dictionary
        # Nested dictionaries of associated classes where reference CIMClassName
        # is the top level key and value is dict with roles as key
        # There is a set of nested dictionaries as follows:
        # value - key is ref classname data is dict with roles as key
        # second - keys are roles, data is list of classnames.
        # [role][ref_classname]
        # [role][ref_classname][result_role].extend(aclns)
        self.assoc_classnames = {}

        # associated instance names dictionary organized by:
        #   - reference_class,
        #   - role,
        #   - associated class
        # NOTE: To account for issues where there is an error getting data from
        # host, the concept of a "None" role exists.
        self.assoc_instnames = {}

        self.source_namespace = source_path.namespace or \
            self.conn.default_namespace
        self.source_host = source_path.host or self.conn.host

        self._build_shrub()

    @property
    def reference_classnames(self):
        """
        Return a list of the reference class names in the current shrub.
        This returns a list of objects of the class pywbem:CIMClassname
        which contains the name, host, and namespace for each class.
        """
        return [cln for cln in self.shrub_dict]

    def _get_reference_roles(self, inst_name):
        """
        Internal method to get the list of roles for an association class.
        This uses the instance get rather than class get because some
        servers may not support class get operation.
        """
        try:
            ref_inst = self.conn.GetInstance(inst_name, LocalOnly=False)
        except CIMError as ce:
            click.echo('Exception ref {}, exception: {}'.format(inst_name, ce))
            return None
        roles = [pname for pname, pvalue in six.iteritems(ref_inst.properties)
                 if pvalue.type == 'reference']
        if self.verbose:
            print('class %s, roles %s' % (inst_name.classname, roles))
        return roles

    def _get_role_result_roles(self, roles, ref_classname):
        """
        Given the reference classname, separate the role and result_role
        parameters and return them. This method determines that the role
        is the call to ReferenceNames that returns references. Result roles
        are the roles that do not return references. Note that there are
        cases where this basic algorithm returns multiple
        """
        rtn_roles = {}
        for tst_role in roles:
            refs = self.conn.ReferenceNames(self.source_path,
                                            Role=tst_role,
                                            ResultClass=ref_classname)
            # TODO where do we account for no references at all.
            # if refs returned, this is valid role that has at least one
            # reference
            if refs:
                rtn_roles[tst_role] = [r for r in roles if r != tst_role]
        if self.verbose:
            print('ResultRoles: class=%s ResultClass=%s ResultRoles=%s'
                  % (self.source_path.classname, ref_classname, rtn_roles))
        return rtn_roles

    def _build_shrub(self):
        """
        Build the internal representation of a tree for the shrub.
        """
        # Build CIMClassname with host, namespace and insert if not
        # already in the class_roles dictionary. Get the instance from
        # the host and  roles from the instance.
        # NOTE: No inst, no roles.
        ref_class_roles = {}
        # TODO handle no refs.
        for ref in self.conn.ReferenceNames(self.source_path):
            cln = CIMClassName(ref.classname, ref.host, ref.namespace)
            if cln not in self.shrub_dict:
                ref_class_roles[cln] = self._get_reference_roles(ref)
        # find the role parameter
        for cln, roles in six.iteritems(ref_class_roles):
            role_dict = self._get_role_result_roles(roles, cln.classname)

            # insert the role and cln into the shrub_dict
            for role, result_roles in role_dict.items():
                if role not in self.shrub_dict:
                    self.shrub_dict[role] = {}
                    if cln not in self.shrub_dict[role]:
                        self.shrub_dict[role][cln] = result_roles

        # Find associated instances/classes
        for role in self.shrub_dict:
            self.assoc_classnames[role] = {}
            self.assoc_instnames[role] = {}
            for ref_classname in self.shrub_dict[role]:
                # Create associator result dictionaries with ref_class as key
                self.assoc_classnames[role][ref_classname] = defaultdict(list)
                self.assoc_instnames[role][ref_classname] = {}

                result_roles = self.shrub_dict[role][ref_classname]

                # get the Associated class names by AssocClass and ResultRole
                assoc_clns = []
                for result_role in result_roles:
                    # disp_result_role = result_role or "None"

                    # Get the Associated instance names
                    anames = self.conn.AssociatorNames(
                        self.source_path,
                        Role=role,
                        AssocClass=ref_classname,
                        ResultRole=result_role)

                    # Get the unique associated classnames
                    new_clns = [
                        CIMClassName(iname.classname, iname.host,
                                     iname.namespace) for iname in anames]

                    assoc_clns.extend(set(new_clns))

                    # add assoc_clns to the assoc_classnames dictionary with
                    # keys
                    #    - ref_classname
                    #    - role (actually the disp role to account for None
                    self.assoc_classnames[role][ref_classname][result_role].extend(assoc_clns)  # noqa: E501

                # Get the associated instance names by AssocClass, role and
                # target name using the aclassnames from above
                for result_role in result_roles:
                    disp_result_role = result_role or "None"
                    for assoc_cln in assoc_clns:
                        anames = self.conn.AssociatorNames(
                            self.source_path,
                            Role=role,
                            AssocClass=ref_classname,
                            ResultRole=result_role,
                            ResultClass=assoc_cln)

                        if disp_result_role not in self.assoc_instnames[role][ref_classname]:  # noqa: E501
                            self.assoc_instnames[role][ref_classname][disp_result_role] = {}  # noqa: E501

                        self.assoc_instnames[role][ref_classname][disp_result_role][assoc_cln] = anames  # noqa: E501

    def build_tree(self, summary):
        """
        Prepare an ascii tree form of the shrub showing the hiearchy of
        components of the shrub. The top is the association source instance.
        The levels of the tree are:
            source instance
                role
                    reference_classe
                        result_role
                            result_classe
                                result_instances
        """
        assoctree = {}
        for role, items in six.iteritems(self.assoc_classnames):
            elementstree = {}
            for ref_cln, roles in six.iteritems(items):
                rrole_dict = {}
                for rrole, assoc_clns in six.iteritems(
                        self.assoc_instnames[role][ref_cln]):
                    assoc_clns_dict = {}
                    for assoc_cln, inst_names in six.iteritems(assoc_clns):
                        disp_assoc_cln = self.simplify_path(assoc_cln)
                        key = "{}(ResultClass)({} insts)". \
                            format(disp_assoc_cln, len(inst_names))
                        if len(inst_names) != 0:
                            assoc_clns_dict[key] = {}
                            if not summary:
                                if inst_names:
                                    inst_dict = {}
                                    for inst_name in inst_names:
                                        inst_name_t = \
                                            self.simplify_path(inst_name)
                                        inst_dict[inst_name_t] = {}
                                    assoc_clns_dict[key] = inst_dict

                    # add the role tree element
                    rrole_disp = "{}(ResultRole)".format(rrole)
                    rrole_dict[rrole_disp] = assoc_clns_dict

                # Add the reference class element. Include namespace if
                # different than conn default namespace
                disp_ref_cln = "{}(AssocClass)". \
                    format(self.simplify_path(ref_cln))

                elementstree[disp_ref_cln] = rrole_dict

            # Add the role component to the tree
            disp_role = "{}(Role)".format(role)
            assoctree[disp_role] = elementstree

        # attach the top of the tree, the source instance path for the
        # shrub.
        display_source_path = self.simplify_path(self.source_path)
        toptree = {display_source_path: assoctree}

        return toptree

    def simplify_path(self, path):
        """
        Simplify the CIMamespace instance defined by path by copying and
        removing the host name and namespace name if they are the same as
        the source instance.  This allows the tree to show only the
        classname for all components of the tree that are in the same
        namespace as the association source instance.
        """
        display_path = path.copy()
        if display_path.host and \
                display_path.host.lower() == self.source_host.lower():
            display_path.host = None
        if display_path.namespace and \
                display_path.namespace.lower() == self.source_namespace.lower():
            display_path.namespace = None
        return display_path

    def display_shrub(self, output_format, summary=None):
        """
        Build the shrub output and display it to the output device based on
        the output_format.
        The default ouput format is ascii tree
        """

        if output_format_is_table(output_format):
            click.echo(self.build_shrub_table(output_format, summary))

        # default is display as ascii tree
        else:
            click.echo(self.build_ascii_display_tree(summary))

    def build_ascii_display_tree(self, summary):
        """
        Build ascii tree display for current shrub.
        Returns an String with the formatted ASCII tree
        """
        tree = self.build_tree(summary)

        tr = LeftAligned()
        return tr(tree)

    def display_dicts(self):
        """
        Development diagnostic to display dictionaries
        """
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        print("ASSOC_CLASSNAMES")
        pp.pprint(self.assoc_classnames)
        print('ASSOC_INST_NAMES')
        pp.pprint(self.assoc_instnames)
        print('SHRUB_DICT')
        pp.pprint(self.shrub_dict)

    def to_wbem_uri_folded(self, path, format='standard', max_len=15):
        # pylint: disable=redefined-builtin
        """
        Return the (untyped) WBEM URI string of this CIM instance path.
        This method modifies the pywbem:CIMInstanceName.to_wbem_uri method
        to return a slightly formated string where components are on
        separate lines if the length is longer than the max_len argument.

        See pywbem.CIMInstanceName.to_wbem_uri for detailed information

        Returns:

          :term:`unicode string`: Untyped WBEM URI of the CIM instance path,
          in the specified format.

        Raises:

          TypeError: Invalid type in keybindings
          ValueError: Invalid format
        """
        path = self.simplify_path(path)
        path_str = "{}".format(path)
        if len(path_str) <= max_len:
            return path_str

        ret = []

        def case(str_):
            """Return the string in the correct lexical case for the format."""
            if format == 'canonical':
                str_ = str_.lower()
            return str_

        def case_sorted(keys):
            """Return the keys in the correct order for the format."""
            if format == 'canonical':
                case_keys = [case(k) for k in keys]
                keys = sorted(case_keys)
            return keys

        if format not in ('standard', 'canonical', 'cimobject', 'historical'):
            raise ValueError(
                _format("Invalid format argument: {0}", format))

        if path.host is not None and format != 'cimobject':
            # The CIMObject format assumes there is no host component
            ret.append('//')
            ret.append(case(path.host))

        if path.host is not None or format not in ('cimobject', 'historical'):
            ret.append('/')

        if path.namespace is not None:
            ret.append(case(path.namespace))

        if path.namespace is not None or format != 'historical':
            ret.append(':')

        ret.append(case(path.classname))

        ret.append('.\n')

        for key in case_sorted(path.keybindings.iterkeys()):
            value = path.keybindings[key]

            ret.append(key)
            ret.append('=')

            if isinstance(value, six.binary_type):
                value = _to_unicode(value)

            if isinstance(value, six.text_type):
                # string, char16
                ret.append('"')
                ret.append(value.
                           replace('\\', '\\\\').
                           replace('"', '\\"'))
                ret.append('"')
            elif isinstance(value, bool):
                # boolean
                # Note that in Python a bool is an int, so test for bool first
                ret.append(str(value).upper())
            elif isinstance(value, (CIMFloat, float)):
                # realNN
                # Since Python 2.7 and Python 3.1, repr() prints float numbers
                # with the shortest representation that does not change its
                # value. When needed, it shows up to 17 significant digits,
                # which is the precision needed to round-trip double precision
                # IEE-754 floating point numbers between decimal and binary
                # without loss.
                ret.append(repr(value))
            elif isinstance(value, (CIMInt, int, _Longint)):
                # intNN
                ret.append(str(value))
            elif isinstance(value, CIMInstanceName):
                # reference
                ret.append('"')
                ret.append(value.to_wbem_uri(format=format).
                           replace('\\', '\\\\').
                           replace('"', '\\"'))
                ret.append('"')
            elif isinstance(value, CIMDateTime):
                # datetime
                ret.append('"')
                ret.append(str(value))
                ret.append('"')
            else:
                raise TypeError(
                    _format("Invalid type {0} in keybinding value: {1!A}={2!A}",
                            type(value), key, value))
            ret.append(',\n')

        del ret[-1]

        return _ensure_unicode(''.join(ret))

    def build_shrub_table(self, output_format, summary):
        """
        Build and return a table representing the shrub. The table
        returned is a string that can be printed to a terminal or or other
        destination.
        """
        # Display shrub as table
        inst_hdr = "Assoc Inst Count" if summary else "Assoc Inst paths"
        headers = ["Role", "Reference Class", "ResultRole",
                   "Associated Class", inst_hdr]
        rows = []
        # assoc_classnames [role]:[ref_clns]:[rrole]:[assoc_clns]
        for role, ref_clns in six.iteritems(self.assoc_classnames):
            for ref_cln in ref_clns:
                ref_clns = self.assoc_classnames[role][ref_cln]
                for rrole, assoc_clns in six.iteritems(ref_clns):
                    for assoc_cln in assoc_clns:
                        inst_names = self.assoc_instnames[role][ref_cln][rrole][assoc_cln]  # noqa E501
                        inst_col = len(inst_names) if summary else \
                            "\n".join(str(self.to_wbem_uri_folded(x))
                            for x in inst_names)  # noqa E128
                        rows.append([role,
                                     self.simplify_path(ref_cln),
                                     rrole,
                                     self.simplify_path(assoc_cln),
                                     inst_col])

        self.display_dicts()
        title = 'Shrub of {}'.format(self.source_path)
        return format_table(rows, headers, title, table_format=output_format)
