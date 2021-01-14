#****************************************************************************
#
# Filename: Houdini/nimMenu.py
# Version:  2.5.0.161013
#
# Copyright (c) 2014-2020 NIM Labs LLC
# All rights reserved.
#
# Use of this software is subject to the terms of the NIM Labs license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
#
# ****************************************************************************

# rohtau v0.2

import hou
import os,sys

action = sys.argv[1]

nimScriptPath = hou.expandString('$NIM_CONNECTOR_ROOT')
sys.path.append(nimScriptPath)
# print "INFO: NIM Script Path: %s" % nimScriptPath


import nim_core.UI as nimUI
import nim_core.nim_api as nimAPI
import nim_core.nim_file as nimFile
import nim_core.nim_win as nimWin
import nim_core.nim_houdini as nimHoudini

reload(nimUI)
reload(nimAPI)
reload(nimFile)
reload(nimWin)

def openFileAction():
    nimUI.mk('FILE')
    hou.ui.setStatusMessage( "NIM: Open File")

def importFileAction():
    nimUI.mk('LOAD', _import=True )
    hou.ui.setStatusMessage( "NIM: Import File")

def refereceFileAction():
    nimUI.mk('LOAD', ref=True)
    hou.ui.setStatusMessage( "NIM: Reference File")

def saveFileAction():
    nimUI.mk('SAVE')
    hou.ui.setStatusMessage( "NIM: Save File")

def saveSelectedAction():
    nimUI.mk( mode='SAVE', _export=True )
    hou.ui.setStatusMessage( "NIM: Save Selected")

def versionUpAction():
    nimAPI.versionUp( padding=nimUI.padding )
    hou.ui.setStatusMessage( "NIM: Version Up Secene")

def publishAction():
    nimUI.mk('PUB')
    hou.ui.setStatusMessage( "NIM: Publish Scene")

def changeUserAction():
    try:
        nimWin.userInfo()
    except Exception, e :
        print 'Sorry, there was a problem choosing NIM user...'
        print '    %s' % traceback.print_exc()
    hou.ui.setStatusMessage( "NIM: change User")
def reloadScriptsAction():
    nimFile.scripts_reload()
    hou.ui.setStatusMessage( "NIM: Reload Scripts")

def dumpPublishInfo():
    print ( 'NIM: dumpPublishInfo' )
    hou.ui.setStatusMessage( "NIM: Dump HIP Publish Information")
    nimHoudini.dump_vars()

def resetPublishInfo():
    print ( 'NIM: resetPublishInfo' )
    hou.ui.setStatusMessage( "NIM: Reset HIP Publish Information")
    nimHoudini.reset_vars()

if action == 'open':
	openFileAction()

if action == 'import':
	importFileAction()

if action == 'ref':
	refereceFileAction()

if action == 'saveas':
	saveFileAction()

if action == 'savesel':
	saveSelectedAction()

if action == 'ver':
	versionUpAction()

if action == 'pub':
	publishAction()

if action == 'user':
    changeUserAction()

if action == 'reload':
	reloadScriptsAction()
