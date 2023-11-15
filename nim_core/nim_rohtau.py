'''
File: nim_rohtau.py
Project: nim_core
File Created: Tuesday, 22nd December 2020 6:38:27 pm
Author: Pablo Gimenez (pablo@rohtau.com)
-----
Last Modified: Thursday, 30 June 2022 01:54:49 GDT
Modified By: Pablo Gimenez (pablo@rohtau.com>)
-----
Copyright 2020 - 2020, rohtau
-----

rohtau interface with NIM and the publishing system in general.
Layer on yop of NIM shared across all supported apps in the pipeline
'''

import os,sys

pythonVersion = sys.version_info.major

if pythonVersion == 3 :
    # Import nim_core for Python3
    from .py3.nim_rohtau import *

else :
    # Import nim_core for Python2
    from py2.nim_rohtau import *
