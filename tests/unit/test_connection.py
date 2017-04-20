#!/usr/bin/env python

# (C) Copyright 2017 IBM Corp.
# (C) Copyright 2017 Inova Development Inc.
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
    Execute and test the validity of the help output from pywbemcli
"""

from __future__ import print_function, absolute_import

import unittest
import shlex
from re import findall
from subprocess import Popen, PIPE


# Map of all tests to be defined.
# each test is defined as
#   name,
#   list of:
#       list of components of pywbemcli help function to execute
#       list of text pieces that must be in result
# TODO ks Mar 17 Some day we should match the entire test result but lets keep
#    it simple until code stabilizes.

SHOW_OUTPUT = ['Default-namespace: root/cimv2',
               'User: fred',
               'Password: password',
               'Timeout: 10',
               'Noverify: True',
               'Certfile: certfile.txt',
               'Certfile: certfile.txt',
               'Name: default']

EXPORT_OUTPUT = ['export PYWBEMCLI_SERVER=http://localhost',
                 'export PYWBEMCLI_DEFAULT_NAMESPACE=root/cimv2',
                 'export PYWBEMCLI_user=fred',
                 'export PYWBEMCLI_user=fred',
                 'export PYWBEMCLI_user=fred',
                 'export PYWBEMCLI_NOVERIFY=True',
                 'export PYWBEMCLI_NOVERIFY=True',
                 'export PYWBEMCLI_KEYFILE=keyfile.txt']
LIST_OUTPUT = ['default']

# the options part is common.  This is just the variable by command part
# NOTE: This is not an ordered test
# TODO figure out how to do create and delete since this is not an
# ordered test
TESTS_MAP = {  # pylint: disable=invalid-name
    'export': ["connection export", EXPORT_OUTPUT],
    "show": ["connection show", SHOW_OUTPUT],
    "set": ["connection set", ['password']],
    "list": ["connection list", LIST_OUTPUT]}


class ContainerMeta(type):
    """Class to define the function to generate test instances"""

    def __new__(mcs, name, bases, dict):  # pylint: disable=redefined-builtin

        def gen_test(test_name, cmd_str, result_data):
            """
            Defines the test method and returns the method.

            Test is the method for each test. Each test builds the pywbemcli
            command executes it and tests the results
            """
            def test(self):  # pylint: disable=missing-docstring
                cmd_opt = '-s http://localhost -u fred -p pw -k keyfile.txt ' \
                          '-c certfile.txt -d root/blah'
                command = 'pywbemcli %s %s' % (cmd_opt, cmd_str)
                args = shlex.split(command)
                proc = Popen(args, stdout=PIPE, stderr=PIPE)
                out, err = proc.communicate()
                exitcode = proc.returncode

                # print(' out %s\n err: %s\n code %s' % (out, err, exitcode))

                self.assertEqual(exitcode, 0, '%s: ExitCode Err, cmd="%s" '
                                 'exitcode %s' % (test_name, command, exitcode))

                self.assertEqual(len(err), 0, '%s stderr not empty.'
                                 % test_name)
                for item in result_data:
                    match_result = findall(item, out)
                    self.assertIsNotNone(match_result,
                                         '%s: Expecting match for %s in '
                                         'output %s' %
                                         (test_name, item, out))
            return test

        for tname, params in TESTS_MAP.iteritems():
            test_name = "test_%s" % tname
            dict[test_name] = gen_test(test_name, params[0], params[1])
        return type.__new__(mcs, name, bases, dict)


class TestsContainer(unittest.TestCase):
    """Container class for all tests"""
    __metaclass__ = ContainerMeta


class OrderedTest(unittest.TestCase):
    """ Some tests must be ordered (create, delete, etc.)
    """

    def test_create_delete(self):
        """ Test create a connection see if it exists and then delete it
        """
        pass

        # Test creating a new connection

        # test show of the new connection

        # test delete the connection

        # test that the connection does not exist


if __name__ == '__main__':

    unittest.main()