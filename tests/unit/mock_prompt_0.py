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
    Python code to mock pywbemcli._common.pywbemcli_prompt. Returns the
    value defined in RETURN_VALUE

    This file was defined to mock the return from pywbemcli instance
    get/delete/... with the simple_assoc_mock_model and return "0" to represent
    the first entry in the displayed output.

    Add this file to the set of mock options and the prompt for picking
    the instance will be output but the prompt for a response from the
    user will be bypassed and the value defined in RETURN_VALUE returned.
"""
from mock import Mock

import pywbemcli._common
RETURN_VALUE = "0"


def mock_prompt(msg):
    """Mock function to replace pywbemcli_prompt and return a value"""
    print(msg)
    return RETURN_VALUE


# pylint: disable=protected-access
pywbemcli._common.pywbemcli_prompt = Mock(side_effect=mock_prompt)