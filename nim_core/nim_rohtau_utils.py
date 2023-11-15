'''
File: nim_rohtau_utils.py
Project: nim_core
File Created: Tuesday, 28 January 2021 12:34:53 pm
Author: Pablo Gimenez (pablo@rohtau.com)
-----
Last Modified: Thursday, 17 March 2022 2:04:57 PM CUT
Modified By: Pablo Gimenez (pablo@rohtau.com>)
-----
Copyright 2020 - 2021, rohtau
-----

Wrapper on top of NIM API
'''

import os,sys

pythonVersion = sys.version_info.major

if pythonVersion == 3 :
    # Import nim_core for Python3
    from .py3.nim_rohtau_utils import *

else :
    # Import nim_core for Python2
    from py2.nim_rohtau_utils import *
