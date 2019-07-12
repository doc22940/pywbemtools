"""
Definition of the DMTF MOF Schema to be used in this testsuite and the
code to install it if not already installed and unzipped.

The version defined below will be installed in the directory defined by
variable TESTSUITE_SCHEMA_DIR below, if that directory is empty or the file
does not exist.

Otherwise, the tests will be executed with that defined version of the
schema.

NOTE: The zip expansion is NOT committed to git, just the original zip file.

To change the schema used:

1. Change the DMTF_SCHEMA_VER varaible to reflect the version of the schema
   that will be the pywbem tests test schema

2. Delete the TESTSUITE_SCHEMA_DIR directory.
   This eliminates the old schema.

3. Execute the test tests/unit/test_server_subcmd.py. This should cause the
   new schema to be downloaded and expanded as part of the test.

5. Add the new DMTF CIM schema zip file to git so that it is persisted for
   Travis, etc. testing
"""

from __future__ import absolute_import, print_function

import os

from pywbem_mock import DMTFCIMSchema


# Change the following variables when a new version of the CIM Schema is used
# and remove the SCHEMA_DIR directory
# This defines the version and the location of the schema zip file on the
# DMTF web site.
# See the page https://www.dmtf.org/standards/cim if there are issues
# downloading a particular version.

# Location of DMTF schema directory used by all tests.
# This directory is permanent and should not be removed.
TESTSUITE_SCHEMA_DIR = os.path.join('tests', 'schema')

# Defines the version of DMTF schema to be downloaded and installed
# To use a different DMTF schema, replace the version number defined in the
# following variable. This must be defined as a tuple to be compatible
# with DMTFCIMSchema.
DMTF_TEST_SCHEMA_VER = (2, 49, 0)


def install_test_dmtf_schema():
    """
    Install the DMTF schema if it is not already installed.  All the
    definitions of the installation are in the module variables.
    The user of ths should need
    """
    schema = DMTFCIMSchema(DMTF_TEST_SCHEMA_VER, TESTSUITE_SCHEMA_DIR)

    return schema