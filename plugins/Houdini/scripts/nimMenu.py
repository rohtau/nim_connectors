#****************************************************************************
#
# Filename: Houdini/nimMenu.py
# Version:  5.0.15.210922
#
# Copyright (c) 2014-2021 NIM Labs LLC
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
import platform
from imp import reload

action = sys.argv[1]

nimScriptPath = hou.expandString('$NIM_CONNECTOR_ROOT')
sys.path.append(nimScriptPath)
# print "INFO: NIM Script Path: %s" % nimScriptPath


import nim_core.UI               as nimUI
import nim_core.nim_api          as nimAPI
import nim_core.nim_file         as nimFile
import nim_core.nim_win          as nimWin
import nim_core.nim_print        as nimP
import nim_core.nim_houdini      as nimHoudini
import nim_core.nim_rohtau       as nimRt
import nim_core.nim_rohtau_utils as nimUtl
import nim_core.nim_rohtau_tc    as nimTc
from nim_core import padding

from rt import pipe
from rt import utils
import rt
from rt.utils import log, getPosixPath

try:
    reload  # Python 2.7
except NameError:
    try:
        from importlib import reload  # Python 3.4+
    except ImportError:
        from imp import reload  # Python 3.0 - 3.3

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
    task = nimRt.pubTask( filepath=hou.hipFile.path(), user=nimAPI.get_user())
    if task:
        h_root = hou.node("/")
        h_root.setUserData("nim_taskID", str(task['taskID']))
    else:
        return False
    return  True

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

def rtSetGlobals( ):
    '''
    Get globals parameters for the show and shot and apply them to our scene
    Globals are gather from environment variables and/or NIM.

    Returns
    ---------
    bool
        True if all went ok
    '''
    print ( 'NIM: Set Globals' )
    hou.ui.setStatusMessage( "NIM: Set Scene Globals")
    nimHoudini.set_globals()

    pass

def rtSetShotRange( ):
    '''
    Get globals parameters for the show and shot and apply them to our scene
    Globals are gather from environment variables and/or NIM.

    Returns
    ---------
    bool
        True if all went ok
    '''
    print ( 'NIM: Set Shot Range' )
    hou.ui.setStatusMessage( "NIM: Set Shot Range")
    nimHoudini.set_shot_range()

    pass

def rtSetPreRoll( ):
    '''
    Set pre roll frames for simulations

    Returns
    ---------
    bool
        True if all went ok
    '''
    print ( 'NIM: Set Pre-Roll' )
    hou.ui.setStatusMessage( "NIM: Set Pre-Roll")
    nimHoudini.set_preroll()

    pass

def rtSimRange( ):
    '''
    Set simulation range in timeline

    Returns
    ---------
    bool
        True if all went ok
    '''
    print ( 'NIM: Set Sim Range' )
    hou.ui.setStatusMessage( "NIM: Set Sim Range")
    nimHoudini.set_sim_range()

    pass
        
def rtRestoreRange( ):
    '''
    Restore previously stached range

    Returns
    ---------
    bool
        True if all went ok
    '''
    print ( 'NIM: Restore Range' )
    hou.ui.setStatusMessage( "NIM: Restore Range")
    nimHoudini.restore_range()

    pass

def rtPublishFlipbook( ):
    '''
    Publish current flipbook in MPlay

    Returns
    ---------
    bool
        True if all went ok
    '''
    print ( 'NIM: Publish Flipbook' )
    hou.ui.setStatusMessage( "NIM: Publish Flipbook")
    pipe.publish_flipbook()

    pass

def rtMplaySetShotRange( ):
    '''
    Get globals parameters for the show and shot and apply them to our Mplay session.
    Globals are gather from environment variables and/or NIM.

    Returns
    ---------
    bool
        True if all went ok
    '''
    print ( 'NIM: Set Mplay Shot Range' )
    hou.ui.setStatusMessage( "NIM: Set Mplay Shot Range")
    # TODO:
    # nimHoudini.set_mplay_shot_range()

    pass

def rtCopyHipPath( ):
    '''
    Copy Hip file path in the clipboard

    Returns
    ---------
    bool
        True if all went ok
    '''
    print ( 'NIM: Copy Hip File Path to Clipboard' )
    hou.ui.setStatusMessage( "NIM: Copy Hip File Path to Clipboard")
    # TODO:
    # nimHoudini.set_mplay_shot_range()
    from PySide2 import QtGui as QtGui2
    path = hou.hipFile.path()
    path = os.path.normpath(path)
    if platform.system() == 'Windows':
        if path.startswith('/') or path.startswith('\\'):
            path = "C:" + path
        path.replace('/', '\\')
    else:
        path = utils.getPosixPath(path)
    cb = QtGui2.QGuiApplication.clipboard()
    cb.clear(mode=cb.Clipboard )
    cb.setText(path, mode=cb.Clipboard)
    
    hou.ui.setStatusMessage("Hip Path copied to the clipboard: %s"%path)

    pass

def rtCopyHipFileID( ):
    '''
    Copy Hip file NIM's FilE ID to the clipboard

    Returns
    ---------
    bool
        True if all went ok
    '''
    h_root = hou.node("/")
    rootdict = h_root.userDataDict()
    if 'nim_jobID' not in rootdict:
        P.error("HIP file doesn't have publishing info. Has this scene been published?")
        return False
    print ( 'NIM: Copy Hip File ID to Clipboard' )
    hou.ui.setStatusMessage( "NIM: Copy Hip File ID to Clipboard")
    fileid  = str(int(rootdict['nim_fileID']))
    from PySide2 import QtGui as QtGui2
    cb = QtGui2.QGuiApplication.clipboard()
    cb.clear(mode=cb.Clipboard )
    cb.setText(fileid, mode=cb.Clipboard)
    
    hou.ui.setStatusMessage("Hip File ID copied to the clipboard: %s"%fileid)

    pass

def rtCheckTimecards():
    '''
    Show a report for today's timecards

    Parameters
    ----------
    

    Returns
    ---------
    

    '''
    hou.ui.setStatusMessage( "NIM: Show Today's Time Cards")
    msg = nimTc.generateTCReport()
    hou.ui.displayMessage(msg, title="Today's Timecards")

    pass

def rtShotbuild():
    '''
    Start shotbuild process

    WIP

    Parameters
    ----------
    

    Returns
    ---------
    

    '''
    log( "NIM: Shotbuild still on the works", severity=rt.Severity.Warning)

    pass

    
def rtShotcam():
    '''
    Load current camera shot if available.
    Look pipe.load_shot_camera() for more info

    Parameters
    ----------
    

    Returns
    ---------
    

    '''
    log( "NIM: Load Shot Cam ")
    pipe.load_shot_camera(openwindow=True)

    pass


if action == 'open':
	openFileAction()
elif action == 'import':
	importFileAction()
elif action == 'ref':
	refereceFileAction()
elif action == 'saveas':
	saveFileAction()
elif action == 'savesel':
	saveSelectedAction()
elif action == 'ver':
	versionUpAction()
elif action == 'pub':
	publishAction()
elif action == 'user':
    changeUserAction()
elif action == 'reload':
	reloadScriptsAction()
elif action == 'dump':
    dumpPublishInfo()
elif action == 'reset':
	resetPublishInfo()
elif action == 'task':
	rtCreateTaskForScript()
elif action == 'info':
	rtShowPubInfo()
elif action == 'setglobals':
	rtSetGlobals()
elif action == 'setshotrange':
	rtSetShotRange()
elif action == 'setpreroll':
	rtSetPreRoll()
elif action == 'setsimrange':
	rtSimRange()
elif action == 'restorerange':
	rtRestoreRange()
elif action == 'publish_flipbook':
	rtPublishFlipbook()
elif action == 'setshotrange_mplay':
	rtMplaySetShotRange()
elif action == 'copypath':
	rtCopyHipPath()
elif action == 'copyfileid':
	rtCopyHipFileID()
elif action == 'timecards':
	rtCheckTimecards()
elif action == 'shotbuild':
	rtShotbuild()
elif action == 'shotcam':
	rtShotcam()

