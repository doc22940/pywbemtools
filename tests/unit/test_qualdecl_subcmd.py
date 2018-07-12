# Copyright 2017 IBM Corp. All Rights Reserved.
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
Tests the qualifier grop of  subcommands
"""
import os
import pytest
from .cli_test_extensions import CLITestsBase

TEST_DIR = os.path.dirname(__file__)

# A mof file that defines basic qualifier decls, classes, and instances
# but not tied to the DMTF classes.
SIMPLE_MOCK_FILE = 'simple_mock_model.mof'

QD_HELP = """Usage: pywbemcli qualifier [COMMAND-OPTIONS] COMMAND [ARGS]...

  Command group to view QualifierDeclarations.

  Includes the capability to get and enumerate CIM qualifier declarations
  defined in the WBEM Server.

  pywbemcli does not provide the capability to create or delete CIM
  QualifierDeclarations

  In addition to the command-specific options shown in this help text, the
  general options (see 'pywbemcli --help') can also be specified before the
  command. These are NOT retained after the command is executed.

Options:
  -h, --help  Show this message and exit.

Commands:
  enumerate  Enumerate CIMQualifierDeclaractions.
  get        Display CIMQualifierDeclaration.
"""

QD_ENUM_HELP = """Usage: pywbemcli qualifier enumerate [COMMAND-OPTIONS]

  Enumerate CIMQualifierDeclaractions.

  Displays all of the CIMQualifierDeclaration objects in the defined
  namespace in the current WBEM Server

Options:
  -n, --namespace <name>  Namespace to use for this operation. If defined that
                          namespace overrides the general options namespace
  -S, --summary           Return only summary of objects (count).
  -h, --help              Show this message and exit.
"""

QD_GET_HELP = """Usage: pywbemcli qualifier get [COMMAND-OPTIONS] QUALIFIERNAME

  Display CIMQualifierDeclaration.

  Displays CIMQualifierDeclaration QUALIFIERNAME for the defined namespace
  in the current WBEMServer

Options:
  -n, --namespace <name>  Namespace to use for this operation. If defined that
                          namespace overrides the general options namespace
  -h, --help              Show this message and exit.
"""

QD_ENUM_MOCK = """Qualifier Abstract : boolean = false,
    Scope(class, association, indication),
    Flavor(EnableOverride, Restricted);

Qualifier Aggregate : boolean = false,
    Scope(reference),
    Flavor(DisableOverride, ToSubclass);

Qualifier Association : boolean = false,
    Scope(association),
    Flavor(DisableOverride, ToSubclass);

Qualifier Description : string,
    Scope(any),
    Flavor(EnableOverride, ToSubclass, Translatable);

Qualifier In : boolean = true,
    Scope(parameter),
    Flavor(DisableOverride, ToSubclass);

Qualifier Indication : boolean = false,
    Scope(class, indication),
    Flavor(DisableOverride, ToSubclass);

Qualifier Key : boolean = false,
    Scope(property, reference),
    Flavor(DisableOverride, ToSubclass);

Qualifier Out : boolean = false,
    Scope(parameter),
    Flavor(DisableOverride, ToSubclass);

Qualifier Override : string,
    Scope(property, reference, method),
    Flavor(EnableOverride, Restricted);

"""

QD_GET_MOCK = """Qualifier Description : string,
    Scope(any),
    Flavor(EnableOverride, ToSubclass, Translatable);

"""
# pylint: disable=line-too-long
QD_GET_MOCK_XML = """<QUALIFIER.DECLARATION ISARRAY="false" NAME="Description" OVERRIDABLE="true" TOSUBCLASS="true" TRANSLATABLE="true" TYPE="string">
    <SCOPE ASSOCIATION="true" CLASS="true" INDICATION="true" METHOD="true" PARAMETER="true" PROPERTY="true" REFERENCE="true"/>
</QUALIFIER.DECLARATION>

"""  # noqa: E501

QD_TBL_OUT = """Qualifier Declarations
+-------------+---------+---------+---------+-------------+-----------------+
| Name        | Type    | Value   | Array   | Scopes      | Flavors         |
+=============+=========+=========+=========+=============+=================+
| Abstract    | boolean | False   | False   | CLASS       | EnableOverride  |
|             |         |         |         | ASSOCIATION | Restricted      |
|             |         |         |         | INDICATION  |                 |
+-------------+---------+---------+---------+-------------+-----------------+
| Aggregate   | boolean | False   | False   | REFERENCE   | DisableOverride |
|             |         |         |         |             | ToSubclass      |
+-------------+---------+---------+---------+-------------+-----------------+
| Association | boolean | False   | False   | ASSOCIATION | DisableOverride |
|             |         |         |         |             | ToSubclass      |
+-------------+---------+---------+---------+-------------+-----------------+
| Description | string  |         | False   | ANY         | EnableOverride  |
|             |         |         |         |             | ToSubclass      |
|             |         |         |         |             | Translatable    |
+-------------+---------+---------+---------+-------------+-----------------+
| In          | boolean | True    | False   | PARAMETER   | DisableOverride |
|             |         |         |         |             | ToSubclass      |
+-------------+---------+---------+---------+-------------+-----------------+
| Indication  | boolean | False   | False   | CLASS       | DisableOverride |
|             |         |         |         | INDICATION  | ToSubclass      |
+-------------+---------+---------+---------+-------------+-----------------+
| Key         | boolean | False   | False   | PROPERTY    | DisableOverride |
|             |         |         |         | REFERENCE   | ToSubclass      |
+-------------+---------+---------+---------+-------------+-----------------+
| Out         | boolean | False   | False   | PARAMETER   | DisableOverride |
|             |         |         |         |             | ToSubclass      |
+-------------+---------+---------+---------+-------------+-----------------+
| Override    | string  |         | False   | PROPERTY    | EnableOverride  |
|             |         |         |         | REFERENCE   | Restricted      |
|             |         |         |         | METHOD      |                 |
+-------------+---------+---------+---------+-------------+-----------------+
"""

QD_STATS_OUT = """Qualifier In : boolean = true,
    Scope(parameter),
    Flavor(DisableOverride, ToSubclass);

  Count    Exc    Time    ReqLen    ReplyLen  Operation
-------  -----  ------  --------  ----------  ------------
      1      0       0         0           0  GetQualifier

"""

OK = True
RUN = True
FAIL = False
MOCK_TEST_CASES = [
    # desc - Description of test
    # args - Dictionary defining input to the command. There are two possible
    #        keywords:
    #        args: List of arguments or string of arguments to append to the
    #            command line after the subcommand
    #        globals - List of arguments or string of arguments to prepend to
    #            the subcommand name.  This allows including global options on
    #            each command.
    # exp_response - Dictionary of expected responses,
    # mock - None or name of files (mof or .py),
    # condition - If True, the test is executed,  Otherwise it is skipped.

    ['Verify qualifier subcommand help response',
     '--help',
     {'stdout': QD_HELP,
      'test': 'lines'},
     None, OK],

    ['Verify qualifier subcommand enumerate  --help response',
     ['enumerate', '--help'],
     {'stdout': QD_ENUM_HELP,
      'test': 'lines'},
     None, OK],

    ['Verify qualifier subcommand enumerate  -h response.',
     ['enumerate', '-h'],
     {'stdout': QD_ENUM_HELP,
      'test': 'lines'},
     None, OK],

    ['Verify qualifier subcommand get  -h response.',
     ['get', '-h'],
     {'stdout': QD_GET_HELP,
      'test': 'lines'},
     None, OK],

    ['Verify qualifier subcommand enumerate returns qual decls.',
     ['enumerate'],
     {'stdout': QD_ENUM_MOCK,
      'test': 'lines'},
     SIMPLE_MOCK_FILE, OK],

    ['Verify qualifier subcommand enumerate with namespace returns qual decls.',
     ['enumerate', '--namespace', 'root/cimv2'],
     {'stdout': QD_ENUM_MOCK,
      'test': 'lines'},
     SIMPLE_MOCK_FILE, OK],

    ['Verify qualifier subcommand enumerate summary returns qual decls.',
     ['enumerate', '--summary'],
     {'stdout': '9 CIMQualifierDeclaration(s) returned',
      'test': 'lines'},
     SIMPLE_MOCK_FILE, OK],

    ['Verify qualifier subcommand get  Description',
     ['get', 'Description'],
     {'stdout': QD_GET_MOCK,
      'test': 'lines'},
     SIMPLE_MOCK_FILE, OK],

    ['Verify qualifier subcommand get invalid qual decl name .',
     ['get', 'NoSuchQualDecl'],
     {'stderr': "Error: CIMError: 6: Qualifier declaration NoSuchQualDecl not "
                "found in namespace root/cimv2.",
      'rc': 1,
      'test': 'lines'},
     SIMPLE_MOCK_FILE, OK],

    ['Verify qualifier subcommand get  Description outputformat xml',
     {'args': ['get', 'Description'],
      'global': ['--output-format', 'xml']},
     {'stdout': QD_GET_MOCK_XML,
      'test': 'lines'},
     SIMPLE_MOCK_FILE, OK],

    ['Verify qualifier subcommand -o grid enumerate produces table out',
     {'args': ['enumerate'],
      'global': ['-o', 'grid']},
     {'stdout': QD_TBL_OUT,
      'rc': 0,
      'test': 'lines'},
     SIMPLE_MOCK_FILE, OK],

    ['Verify qualifier subcommand enumerate invalid namespace Fails',
     ['enumerate', '--namespace', 'root/blah'],
     {'stderr': "Error: CIMError: 3: Namespace root/blah not found for "
                "qualifiers",
      'rc': 1,
      'test': 'lines'},
     SIMPLE_MOCK_FILE, OK],

    ['Verify qualifier subcommand -T (statistics) gets stats output',
     {'args': ['get', 'IN'],
      'global': ['-T']},
     {'stdout': QD_STATS_OUT,
      'rc': 0,
      'test': 'lines'},
     SIMPLE_MOCK_FILE, OK],

    ['Verify qualifier subcommand --timestats gets stats output',
     {'args': ['get', 'IN'],
      'global': ['--timestats']},
     {'stdout': QD_STATS_OUT,
      'rc': 0,
      'test': 'lines'},
     SIMPLE_MOCK_FILE, OK],
]


class TestSubcmdQualifiers(CLITestsBase):
    """
    Test all of the qualifiers subcommand variations.
    """
    subcmd = 'qualifier'

    @pytest.mark.parametrize(
        "desc, args, exp_response, mock, condition",
        MOCK_TEST_CASES)
    def test_qualdecl(self, desc, args, exp_response, mock, condition):
        """
        Common test method for those subcommands and options in the
        class subcmd that can be tested.  This includes:

          * Subcommands like help that do not require access to a server

          * Subcommands that can be tested with a single execution of a
            pywbemcli command.
        """
        env = None
        self.mock_subcmd_test(desc, self.subcmd, args, env, exp_response,
                              mock, condition)