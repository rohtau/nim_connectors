#!/bin/env python
#******************************************************************************
#
# Filename:    projectHook.py
# Version:     v5.0.11.210722
# Compatible:  Python 3.x
#
# Copyright (c) 2014-2021 NIM Labs LLC
# All rights reserved.
#
# Use of this software is subject to the terms of the NIM Labs license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# *****************************************************************************

debug=True

import os, sys
import re
from pprint import pprint, pformat

# NIM imports
import nim_core.nim_print        as nimP
import nim_core.nim              as Nim
import nim_core.nim_file         as nimF
import nim_core.nim_api          as nimAPI
import nim_core.nim_win          as nimWin
import nim_core.nim_rohtau       as nimRt
import nim_core.nim_rohtau_utils as nimUtl
from nim_core import padding 

import flame

nim_app = 'Flame'
os.environ['NIM_APP'] = nim_app

# Relative path to append for NIM Scripts
nimFlamePythonPath = os.path.dirname(os.path.realpath(__file__))
nimFlamePythonPath = nimFlamePythonPath.replace('\\','/')
nimScriptPath = re.sub(r"\/plugins/Flame/python/py3$", "", nimFlamePythonPath)
nimFlamePresetPathBase = os.path.join(re.sub(r"\/python/py3$", "", nimFlamePythonPath),'presets')

try :
    flame_major_version = flame.get_version_major()
    nimFlamePresetPath = os.path.join(nimFlamePresetPathBase, flame_major_version)

    if os.path.isdir(nimFlamePresetPath) == False :
        nimFlamePresetPath = os.path.join(nimFlamePresetPathBase,'_default')
except :
    nimFlamePresetPath = os.path.join(nimFlamePresetPathBase,'_default')

sys.path.append(nimScriptPath)

import flame_widgets


# Hook called when the user loads a project in the application.
# project_name : Name of the loaded project -- String.
def project_changed(project_name):
    '''
    print("project_changed - start >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    os.environ['NIM_FLAME_PROJECT'] = str(project_name)
    if debug :
        print(project_name)
    print("project_changed - end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    '''
    nimP.info("New project loaded: %s"%project_name)
    os.environ['NIM_FLAME_PROJECT'] = project_name
    flameuser = flame.users.current_user.name
    nimuser = nimUtl.get_nim_user()
    nimuser = nimuser.split('@')[0]
    if nimuser != flameuser:
        nimP.warning("Flame user (%s) is not the same as NIM user (%s). Please check you user name in Flame and try to match NIM user name"%(flameuser, nimuser))
        msg = "Flame user (%s) is not the same as NIM user (%s).\nCheck you are using the correct Flame user and NIM user.\nPlease change your Flame user name to match your NIM user name"%(flameuser, nimuser)
        # nimWin.popup( title='Flame User', msg=msg, type='ok')
        flame_widgets.FlameMessageWindow('Flame User', 'warning', msg)


    pass


# Hook called when the user loads a project in the application.
# info [Dictionary] [Modifiable]
#    Information about project
#
#    Keys:
#
#    flameProjectName: [String]
#       Name of the flame project.
#
#    shotgunProjectName: [String] [Modifiable]
#       Name of the shotgun projet it is linked with.
#       Will be empty if there is no link yet.
#
def project_changed_dict(info):
    pass


# Hook called when application is fully initialized
# project_name: the project that was loaded -- String
def app_initialized(project_name):
    pass


# Hook called after a project has been saved
#
# project_name: the project that was saved -- String
# save_time    : time to save the project (in seconds) -- Float
# is_auto_save : true if save was automatically initiated,
#                false if user initiated -- Bool
def project_saved(project_name, save_time, is_auto_save):
    pass

