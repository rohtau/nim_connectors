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
from imp import reload

action = sys.argv[1]

nimScriptPath = hou.expandString('$NIM_CONNECTOR_ROOT')
sys.path.append(nimScriptPath)
# print "INFO: NIM Script Path: %s" % nimScriptPath


import nim_core.UI as nimUI
import nim_core.nim_api as nimAPI
import nim_core.nim_file as nimFile
import nim_core.nim_win as nimWin
import nim_core.nim_print as nimP
import nim_core.nim_houdini as nimHoudini
import nim_core.nim_rohtau as nimRt
import nim_core.nim_rohtau_utils as nimUtl
from nim_core import padding

reload(nimUI)
reload(nimAPI)
reload(nimFile)
reload(nimWin)
reload(nimP)

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
    nimAPI.versionUp( padding=padding )
    hou.ui.setStatusMessage( "NIM: Version Up Secene")

def publishAction():
    nimUI.mk('PUB')
    hou.ui.setStatusMessage( "NIM: Publish Scene")

def changeUserAction():
    try:
        nimWin.userInfo()
    except Exception as e :
        print('Sorry, there was a problem choosing NIM user...')
        print('    %s' % traceback.print_exc())
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

def rtCreateTaskForScript():
    '''
    Create an appropriate task in the shot/asset for this user according with the task used by the script filename
    
    Returns
    -------
    bool
        True if task was created correctly or if it already exists. False if task creation failed
    '''
    return nimRt.pubTask( filepath=hou.hipFile().path(), user=getpass.getuser())

def rtShowPubInfo():
    '''
    Show scene publishing comments
    '''
    h_root = hou.node("/")

    nim_fileID = h_root.userData("nim_fileID")
    if nim_fileID is not None and nim_fileID.isdigit():
        return nimRt.showPubInfo(int(nim_fileID), hou.isUIAvailable())
    else:
        hou.ui.displayMessage('Looks like this HIP file hasn\'t been published. Can\'t retrieve publishing ID',
                              title="Publish Error", severity=hou.severityType.Error, 
                              help='Check whether or not the file has been published correctly: rohtau->NIM->Dump Publish Info.\bPublish scene using rohtau->Save As')
        nimP.error('Looks like this HIP file hasn\'t been published. Check whether or not the file has been published correctly: rohtau->NIM->Dump Publish Info')

        return



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

if action == 'dump':
    dumpPublishInfo()

if action == 'reset':
	resetPublishInfo()

if action == 'task':
	rtCreateTaskForScript()

if action == 'info':
	rtShowPubInfo()
