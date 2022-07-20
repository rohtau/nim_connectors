#!/usr/bin/env python
#******************************************************************************
#
# Filename: nim_maya.py
# Version:  v5.1.2.220314
#
# Copyright (c) 2014-2022 NIM Labs LLC
# All rights reserved.
#
# Use of this software is subject to the terms of the NIM Labs license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# *****************************************************************************

#  General Imports :
import os
import sys
import platform
import traceback
import threading
import time
import json
import getpass
from pprint import pprint, pformat
# NIM imports
try:
    import nim              as Nim
    import nim_file         as F
    import nim_print        as P
    import nim_api          as Api
    import nim_rohtau       as Rt
    import nim_rohtau_utils as Utl
    import nim_rohtau_tc    as Tc
except ImportError as e:
    from . import nim              as Nim
    from . import nim_file         as F
    from . import nim_print        as P
    from . import nim_api          as Api
    from . import nim_rohtau       as Rt
    from . import nim_rohtau_utils as Utl
    from . import nim_rohtau_tc    as Tc
#  Maya Imports :
import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om
from pymel.core import *
#  Import Python GUI packages :
try : 
    from PySide2 import QtWidgets as QtGui
    from PySide2 import QtCore
except ImportError :
    try : 
        from PySide import QtCore, QtGui
    except ImportError :
        try : 
            from PyQt4 import QtCore, QtGui
        except ImportError : 
            try :
                from PyQt5 import QtWidgets as QtGui
                from PyQt5 import QtCore
            except ImportError :
                print("NIM: Failed to load UI Modules - Maya")
# Import rohtau's mayacore
import pipe

#  Variables :
from .import version 
from .import winTitle 
from .import mwtt

# Globals
fps_names = {
    15 : 'game',
    24 : 'film',
    25 : 'pal',
    30 : 'ntsc',
    48 : 'show',
    50 : 'palf',
    60 : 'ntscf'
}




def get_mainWin() :
    'Returns the name of the main Maya window'
    import maya.OpenMayaUI as omUI
    #from PySide import QtGui
    try : 
        from PySide2 import QtWidgets as QtGui
    except ImportError :
        try : 
            from PySide import QtGui
        except ImportError :
            pass
    try:
        from shiboken2 import wrapInstance
    except ImportError :
        from shiboken import wrapInstance
    #  Get the main maya window as a QMainWindow instance :
    mayaWin=wrapInstance( int( omUI.MQtUtil.mainWindow() ), QtGui.QWidget )
    return mayaWin

def set_vars( nim=None ) :
    'Add variables to Maya Render Globals'
    
    mc.undoInfo(openChunk=True)

    P.info( '\nSetting Render Globals variables...' )
    
    #  User :
    userInfo=nim.userInfo()
    if not mc.attributeQuery( 'nim_user', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_user', dt='string')
    mc.setAttr( 'defaultRenderGlobals.nim_user', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_user', userInfo['name'], type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_user', lock=True, keyable=False)
    #  User ID :
    if not mc.attributeQuery( 'nim_userID', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_userID', dt='string')
    mc.setAttr( 'defaultRenderGlobals.nim_userID', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_userID', userInfo['ID'], type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_userID', lock=True, keyable=False)
    #  Tab/Class :
    if not mc.attributeQuery( 'nim_class', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_class', dt='string')
    mc.setAttr( 'defaultRenderGlobals.nim_class', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_class', nim.tab(), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_class', lock=True, keyable=False)
    #  Server :
    if not mc.attributeQuery( 'nim_server', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_server', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_server', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_server', nim.server(), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_server', lock=True, keyable=False)
    #  Server ID :
    if not mc.attributeQuery( 'nim_serverID', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_serverID', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_serverID', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_serverID', str(nim.ID('server')), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_serverID', lock=True, keyable=False)
    #  Job :
    if not mc.attributeQuery( 'nim_jobName', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_jobName', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_jobName', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_jobName', nim.name('job'), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_jobName', lock=True, keyable=False)
    #  Job ID :
    if not mc.attributeQuery( 'nim_jobID', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_jobID', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_jobID', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_jobID', str(nim.ID('job')), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_jobID', lock=True, keyable=False)
    #  Show :
    if not mc.attributeQuery( 'nim_showName', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_showName', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_showName', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_showName', nim.name('show'), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_showName', lock=True, keyable=False)
    #  Show ID :
    if nim.tab()=='SHOT' :
        if not mc.attributeQuery( 'nim_showID', node='defaultRenderGlobals', exists=True) :
            mc.addAttr( 'defaultRenderGlobals', longName='nim_showID', dt="string")
        mc.setAttr( 'defaultRenderGlobals.nim_showID', lock=False)
        mc.setAttr( 'defaultRenderGlobals.nim_showID', str(nim.ID('show')), type='string' )
        mc.setAttr( 'defaultRenderGlobals.nim_showID', lock=True, keyable=False)
    #  Shot :
    if not mc.attributeQuery( 'nim_shot', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_shot', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_shot', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_shot', str(nim.name('shot')), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_shot', lock=True, keyable=False)
    #  Shot ID :
    if not mc.attributeQuery( 'nim_shotID', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_shotID', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_shotID', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_shotID', str(nim.ID('shot')), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_shotID', lock=True, keyable=False)
    #  Asset :
    if nim.tab()=='ASSET' :
        if not mc.attributeQuery( 'nim_asset', node='defaultRenderGlobals', exists=True) :
            mc.addAttr( 'defaultRenderGlobals', longName='nim_asset', dt="string")
        mc.setAttr( 'defaultRenderGlobals.nim_asset', lock=False)
        mc.setAttr( 'defaultRenderGlobals.nim_asset', str(nim.name('asset')), type='string' )
        mc.setAttr( 'defaultRenderGlobals.nim_asset', lock=True, keyable=False)
    #  Asset ID :
    if nim.tab()=='ASSET' :
        if not mc.attributeQuery( 'nim_assetID', node='defaultRenderGlobals', exists=True) :
            mc.addAttr( 'defaultRenderGlobals', longName='nim_assetID', dt="string")
        mc.setAttr( 'defaultRenderGlobals.nim_assetID', lock=False)
        mc.setAttr( 'defaultRenderGlobals.nim_assetID', str(nim.ID('asset')), type='string' )
        mc.setAttr( 'defaultRenderGlobals.nim_assetID', lock=True, keyable=False)
    #  File ID :
    if not mc.attributeQuery( 'nim_fileID', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_fileID', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_fileID', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_fileID', str(nim.ID('ver')), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_fileID', lock=True, keyable=False)
    #  Shot/Asset Name :
    if not mc.attributeQuery( 'nim_name', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_name', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_name', lock=False)
    if nim.tab()=='SHOT' :
        mc.setAttr( 'defaultRenderGlobals.nim_name', nim.name('shot'), type='string' )
    elif nim.tab()=='ASSET' :
        mc.setAttr( 'defaultRenderGlobals.nim_name', nim.name('asset'), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_name', lock=True, keyable=False)
    #  Basename :
    if not mc.attributeQuery( 'nim_basename', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_basename', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_basename', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_basename', nim.name('base'), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_basename', lock=True, keyable=False)
    #  Task :
    if not mc.attributeQuery( 'nim_task', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_task', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_task', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_task', nim.name( elem='task' ), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_task', lock=True, keyable=False)
    if not mc.attributeQuery( 'nim_type', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_type', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_type', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_type', nim.name( elem='task' ), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_type', lock=True, keyable=False)
    #  Task ID :
    if not mc.attributeQuery( 'nim_taskID', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_taskID', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_taskID', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_taskID', str(nim.ID( elem='task' )), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_taskID', lock=True, keyable=False)
    if not mc.attributeQuery( 'nim_typeID', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_typeID', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_typeID', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_typeID', str(nim.ID( elem='task' )), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_typeID', lock=True, keyable=False)
    #  Task Folder :
    if not mc.attributeQuery( 'nim_typeFolder', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_typeFolder', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_typeFolder', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_typeFolder', str(nim.taskFolder()), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_typeFolder', lock=True, keyable=False)
    #  Tag :
    if not mc.attributeQuery( 'nim_tag', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_tag', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_tag', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_tag', nim.name('tag'), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_tag', lock=True, keyable=False)
    #  File Type :
    if not mc.attributeQuery( 'nim_fileType', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_fileType', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_fileType', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_fileType', nim.fileType(), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_fileType', lock=True, keyable=False)
    #  Job Path :
    if not mc.attributeQuery( 'nim_jobPath', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_jobPath', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_jobPath', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_jobPath', str(nim.jobPath()), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_jobPath', lock=True, keyable=False)
    #  Shot Path :
    if not mc.attributeQuery( 'nim_shotPath', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_shotPath', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_shotPath', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_shotPath', str(nim.shotPath()), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_shotPath', lock=True, keyable=False)
    #  Render Path :
    if not mc.attributeQuery( 'nim_renderPath', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_renderPath', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_renderPath', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_renderPath', str(nim.renderPath()), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_renderPath', lock=True, keyable=False)
    #  Comp Path :
    if not mc.attributeQuery( 'nim_compPath', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_compPath', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_compPath', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_compPath', str(nim.compPath()), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_compPath', lock=True, keyable=False)
    #  Plates Path :
    if not mc.attributeQuery( 'nim_platesPath', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_platesPath', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_platesPath', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_platesPath', str(nim.platesPath()), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_platesPath', lock=True, keyable=False)
    #  Pub Elements Types :
    if not mc.attributeQuery( 'nim_pubElements', node='defaultRenderGlobals', exists=True) :
        mc.addAttr( 'defaultRenderGlobals', longName='nim_pubElements', dt="string")
        # mc.scrollField( 'defaultRenderGlobals', longName='nim_pubElements', dt="string")
    mc.setAttr( 'defaultRenderGlobals.nim_pubElements', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_pubElements', str(nim.get_elementTypes()), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_pubElements', lock=True, keyable=False)
    
    P.info('    Completed setting NIM attributes on the defaultRenderGlobals node.')
    #nim.Print()
    
    # Open/Close scene script nodes
    if not mc.objExists( 'rtOpenScene' ) :
        openSceneNodeName = cmds.scriptNode( st=2, bs='import nim_core.nim_maya as M; M.rtOpenScene()', n='rtOpenScene', stp='python')

    mc.undoInfo(closeChunk=True)
    return

def set_fileid_var( fileid ):
    '''
    Set FileID data.
    Needed to update scene after it has been published
    '''
    mc.setAttr( 'defaultRenderGlobals.nim_fileID', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_fileID', str(fileid), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_fileID', lock=True, keyable=False)

    return True

def set_taskid_var( taskid ):
    '''
    Set publishing task id
    Used as the default task to publish data to in case it need an associated task (renders)

    Parameters
    ----------
    taskid : int
        Id for the publishing task

    Returns
    -------
    int
        Task Id as int, 0 or False if error.
    '''
    mc.setAttr( 'defaultRenderGlobals.nim_taskID', lock=False)
    mc.setAttr( 'defaultRenderGlobals.nim_taskID', str(taskid), type='string' )
    mc.setAttr( 'defaultRenderGlobals.nim_taskID', lock=True, keyable=False)
    return True

def get_vars( nim=None ) :
    'Gets NIM settings from the defaultRenderGlobals node in Maya.'
    
    mc.undoInfo(openChunk=True)

    P.info('Getting information from NIM attributes on the defaultRenderGlobals node...')
    
    #  User :
    if mc.objExists( 'defaultRenderGlobals.nim_user' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_user' )
        P.debug( 'User = %s' % value )
        nim.set_user( userName=value )
    #  User ID :
    if mc.objExists( 'defaultRenderGlobals.nim_userID' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_userID' )
        P.debug( 'User ID = %s' % value )
        nim.set_userID( userID=value )

    #  Tab/Class :
    if mc.objExists( 'defaultRenderGlobals.nim_class' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_class' )
        P.debug( 'Tab = %s' % value )
        nim.set_tab( value )

    #  Server :
    if mc.objExists( 'defaultRenderGlobals.nim_server' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_server' )
        P.debug( 'Server = %s' % value )
        nim.set_server( path=value )
    #  Server ID :
    if mc.objExists( 'defaultRenderGlobals.nim_serverID' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_serverID' )
        P.debug( 'Server ID = %s' % value )
        nim.set_ID( elem='server', ID=value )

    #  Job :
    if mc.objExists( 'defaultRenderGlobals.nim_jobName' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_jobName' )
        P.debug( 'Job = %s' % value )
        nim.set_name( elem='job', name=value )
    #  Job ID :
    if mc.objExists( 'defaultRenderGlobals.nim_jobID' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_jobID' )
        P.debug( 'Job ID = %s' % value )
        nim.set_ID( elem='job', ID=value )

    #  Show :
    if mc.objExists( 'defaultRenderGlobals.nim_showName' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_showName' )
        P.debug( 'Show = %s' % value )
        nim.set_name( elem='show', name=value )
    #  Show ID :
    if mc.objExists( 'defaultRenderGlobals.nim_showID' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_showID' )
        P.debug( 'Show ID = %s' % value )
        nim.set_ID( elem='show', ID=value )

    #  Shot :
    if mc.objExists( 'defaultRenderGlobals.nim_shot' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_shot' )
        P.debug( 'Shot = %s' % value )
        nim.set_name( elem='shot', name=value )
    #  Shot ID :
    if mc.objExists( 'defaultRenderGlobals.nim_shotID' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_shotID' )
        P.debug( 'Shot ID = %s' % value )
        nim.set_ID( elem='shot', ID=value )
    #  Asset :
    if mc.objExists( 'defaultRenderGlobals.nim_asset' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_asset' )
        P.debug( 'Asset = %s' % value )
        nim.set_name( elem='asset', name=value )
    #  Asset ID :
    if mc.objExists( 'defaultRenderGlobals.nim_assetID' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_assetID' )
        P.debug( 'Asset ID = %s' % value )
        nim.set_ID( elem='asset', ID=value )

    #  File ID :
    '''
    if mc.attributeQuery( 'defaultRenderGlobals.nim_fileID' ) :
        value=mc.attributeQuery( 'nim_fileID', node='defaultRenderGlobals' )
        P.debug( 'Class = %s' % value )
        nim.set_tab( tab=value )
    '''
    if mc.objExists( 'defaultRenderGlobals.nim_fileID' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_fileID' )
        if nim_fileID is not None:
            nim.set_ID( elem='file', ID=nim_fileID )
            P.info('Reading nim_fileID')
        else:
            P.error('Failed reading nim_fileID')

    #  Shot/Asset Name :
    if mc.objExists( 'defaultRenderGlobals.nim_name' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_name' )
        #  Determine what the tab is set to :
        if nim.tab()=='SHOT' :
            P.debug( 'Shot Name = %s' % value )
            #  No corresponding NIM attribute :
            #nim.set_tab( value )
        elif nim.tab()=='ASSET' :
            P.debug( 'Asset Name = %s' % value )
            #  No corresponding NIM attribute :
            #nim.set_tab( value )
    #  Basename :
    if mc.objExists( 'defaultRenderGlobals.nim_basename' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_basename' )
        P.debug( 'Basename = %s' % value )
        nim.set_name( elem='base', name=value )
    #  Task :
    if mc.objExists( 'defaultRenderGlobals.nim_type' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_type' )
        P.debug( 'Task = %s' % value )
        nim.set_name( elem='task', name=value )
    #  Task ID :
    if mc.objExists( 'defaultRenderGlobals.nim_typeID' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_typeID' )
        P.debug( 'Task ID = %s' % value )
        nim.set_ID( elem='task', ID=value )
    #  Task Folder :
    if mc.objExists( 'defaultRenderGlobals.nim_typeFolder' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_typeFolder' )
        P.debug( 'Task Folder = %s' % value )
        nim.set_taskFolder( folder=value )
    #  Tag :
    if mc.objExists( 'defaultRenderGlobals.nim_tag' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_tag' )
        P.debug( 'Tag = %s' % value )
        nim.set_name( elem='tag', name=value )
    #  File Type :
    if mc.objExists( 'defaultRenderGlobals.nim_fileType' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_fileType' )
        P.debug( 'File Type = %s' % value )
        nim.set_name( elem='file', name=value )
    
    #  Print dictionary :
    #P.info('\nNIM Dictionary from get vars...')
    #nim.Print()

    # Open/Close scene script nodes
    if not mc.objExists( 'rtOpenScene' ) :
        openSceneNodeName = cmds.scriptNode( st=2, bs='import nim_core.nim_maya as M; M.rtOpenScene()', n='rtOpenScene', stp='python')

    mc.undoInfo(closeChunk=True)
    return

def get_taskid_var():
    '''
    Get publishing task id
    Used as the default task to publish data to in case it need an associated task (renders)

    Returns
    -------
    int
        Task Id as int, 0 or False if error.
    '''
    if mc.objExists( 'defaultRenderGlobals.nim_taskID' ) :
        value=mc.getAttr( 'defaultRenderGlobals.nim_taskID' )
        P.debug( 'Task ID = %s' % value )
        return int(value)
    else:
        P.error("Can't get Task ID, key doesn't exists, has this scene publish information?")
        return False

def stash_frame_range():
    '''
    Store current frame and display range in envars for future restore using restore_range

    Parameters
    ----------


    Returns
    ---------
    bool
        True if everything went ok.

    '''
    # framerange = hou.playbar.frameRange()
    # displayrange = hou.playbar.playbackRange()
    playstart = mc.playbackOptions(minTime=True, query=True)
    playend   = mc.playbackOptions(maxTime=True, query=True)
    start     = mc.playbackOptions(ast=True, query=True)
    end       = mc.playbackOptions(aet=True, query=True)
    mel.putenv('SHOTSTART_STASH',    str(int(start)))
    mel.putenv('SHOTEND_STASH',      str(int(end)))
    mel.putenv('SHOTSTARTCUT_STASH', str(int(playstart)))
    mel.putenv('SHOTENDCUT_STASH',   str(int(playend)))

    return True


def set_globals():
    '''
    Get globals parameters for the show and shot and apply them to our scene
    Globals are gather from environment variables and/or NIM.

    Globals
    --------
    - Render resolution
    - FPS
    - Shot range

    Parameters
    ----------

    Returns
    ---------
    bool
        True if all went ok
    '''
    #  Job ID :
    if not mc.objExists( 'defaultRenderGlobals.nim_jobID' ) :
        P.error("Maya scene doesn't have publishing info. Has this scene been published?")
        return False
    jobid = int(mc.getAttr( 'defaultRenderGlobals.nim_jobID' ))
    jobglobals = Utl.getShowGlobals( jobid )

    msg = ""

    # Set output format.
    # If format doesn't match, create format for show.
    if 'output_res' in jobglobals:
        mel.putenv('SHOWOUTPUT', jobglobals['output_res'])
        (resx, resy) = jobglobals['output_res'].split('x')
        resx = int(resx)
        resy = int(resy)
        mc.setAttr( 'defaultResolution.width', resx)
        mc.setAttr( 'defaultResolution.height', resy)
        msg += "- Render resolution set to: %dx%d\n"%(resx,resy)

    
    # Set FPS
    if 'fps' in jobglobals:
        mel.putenv('FPS', str(jobglobals['fps']))
        # cmds.currentUnit( time='ntsc' )
        if jobglobals['fps'] in fps_names:
            mel.currentUnit( time=fps_names[jobglobals['fps']] )
        msg += "- FPS set to %d\n"%jobglobals['fps']

    # Shot
    # Set frame range. Check if frame range is actually y bigger in any of sides,
    # start or end
    shotid = int(mc.getAttr( 'defaultRenderGlobals.nim_shotID' )) if mc.getAttr( 'defaultRenderGlobals.nim_class' ) == 'SHOT' else int(mc.getAttr( 'defaultRenderGlobals.nim_assetID' ))
    shotglobals = Utl.getShotGlobals( shotid, entity_type=mc.getAttr( 'defaultRenderGlobals.nim_class' ))

    # print("Shot Globals")
    # print(pformat(shotglobals))
    if 'frames' in shotglobals:
        # Set frame range and display range. Move to first display frame. Disable cooking
        frames = shotglobals['frames'] if shotglobals['frames'] else default_frame_range
        # Save current range
        stash_frame_range()
        first = 1001 # We always start at 1001 by convention
        last = 1001 + frames - 1
        mc.playbackOptions(ast=first)
        mc.playbackOptions(aet=last)
        mc.playbackOptions(minTime=first+shotglobals['handles'])
        mc.playbackOptions(maxTime=last-shotglobals['handles'])
        mc.playbackOptions(maxTime=last-shotglobals['handles'])
        mel.currentTime( first+shotglobals['handles'] )
        mel.putenv('SHOTSTART', str(first))
        mel.putenv('SHOTEND', str(last))
        mel.putenv('SHOTSTARTCUT', str(first+shotglobals['handles']))
        mel.putenv('SHOTENDCUT', str(last-shotglobals['handles']))
        mel.putenv('SHOTFRAMES', str(frames))
        mel.putenv('SHOTHANDLES', str(shotglobals['handles']))
        if not mel.getenv('SHOTPREROLL'):
            mel.putenv('SHOTPREROLL', str(0))
        mel.putenv('SHOTSIMSTART', str(first-int(mel.getenv('SHOTPREROLL'))))


        msg += "- Frame range set to %d-%d. Shot Range (with handles): %d - %d\n"%(first, last, first+shotglobals['handles'], 
                                                                                   last-shotglobals['handles'])
    else:
        msg += "- WARNING: No Frame Range information for this shot"

    if msg:
        msg = "The next changes have been apply in the script:\n\n" + msg
        mel.confirmDialog(title='Set Globals ...', message=msg, button=['Ok'], defaultButton='Ok')


    return True

def set_shot_range():
    '''
    Set scene time range to shot frames

    Parameters
    ----------

    Returns
    ---------
    bool
        True if all went ok
    '''
    #  Job ID :
    if not mc.objExists( 'defaultRenderGlobals.nim_jobID' ) :
        P.error("Maya scene doesn't have publishing info. Has this scene been published?")
        return False
    jobid = int(mc.getAttr( 'defaultRenderGlobals.nim_jobID' ))
    jobglobals = Utl.getShowGlobals( jobid )

    # Shot
    # Set frame range. Check if frame range is actually y bigger in any of sides,
    # start or end
    shotid = int(mc.getAttr( 'defaultRenderGlobals.nim_shotID' )) if mc.getAttr( 'defaultRenderGlobals.nim_class' ) == 'SHOT' else int(mc.getAttr( 'defaultRenderGlobals.nim_assetID' ))
    frames  = int(mel.getenv('SHOTFRAMES'))
    handles = int(mel.getenv('SHOTHANDLES'))
    if not frames and mc.objExists( 'defaultRenderGlobals.nim_frames'):
        frames = int(mc.getAttr( 'defaultRenderGlobals.nim_frames'))
    if not handles and mc.objExists( 'defaultRenderGlobals.nim_handles'):
        handles = int(mc.getAttr( 'defaultRenderGlobals.nim_handles'))
    if frames :
        stash_frame_range()
        first = 1001 # We always start at 1001 by convention
        last = 1001 + frames - 1
        mc.playbackOptions(ast=first)
        mc.playbackOptions(aet=last)
        mc.playbackOptions(minTime=first+handles)
        mc.playbackOptions(maxTime=last-handles)
        mel.currentTime( first+handles )
        msg = "Frame range set to %d-%d. Shot Range (with handles): %d - %d\n"%(first, last, first+handles, last-handles)
        om.MGlobal.displayInfo(msg)
    else:
        msg = "Couldn't find shot frame range information, SHOTFRAMES and/or SHOTHANDLES are missing. Please run Set Globals to update shot information."
        om.MGlobal.displayError(msg)
        mel.confirmDialog(title='Set Shot Range ...', message=msg, button=['Ok'], defaultButton='Ok')
        return False

    return True


def set_preroll():
    '''
    Set scene simulation preroll

    Parameters
    ----------

    Returns
    ---------
    bool
        True if all went ok
    '''
    #  Job ID :
    if not mc.objExists( 'defaultRenderGlobals.nim_jobID' ) :
        P.error("Maya scene doesn't have publishing info. Has this scene been published?")
        return False
    jobid = int(mc.getAttr( 'defaultRenderGlobals.nim_jobID' ))
    jobglobals = Utl.getShowGlobals( jobid )

    # Shot
    # Set frame range. Check if frame range is actually y bigger in any of sides,
    # start or end
    shotid = int(mc.getAttr( 'defaultRenderGlobals.nim_shotID' )) if mc.getAttr( 'defaultRenderGlobals.nim_class' ) == 'SHOT' else int(mc.getAttr( 'defaultRenderGlobals.nim_assetID' ))
    frames  = int(mel.getenv('SHOTFRAMES'))
    handles = int(mel.getenv('SHOTHANDLES'))
    if frames:
        preroll = int(mel.getenv('SHOTPREROLL'))
        if not preroll:
            preroll=0
        result = mc.promptDialog(
                title='Set Scene Pre-Roll for Simulation ...',
                message='Pre-Roll Frames',
                text=str(preroll),
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')

        if result == 'OK':
            preroll  = int(mc.promptDialog(query=True, text=True))
            stash_frame_range()
            first = 1001 # We always start at 1001 by convention
            last = 1001 + frames - 1
            first = first - preroll
            mc.playbackOptions(ast=first)
            mc.playbackOptions(aet=last)
            mc.playbackOptions(minTime=first)
            mc.playbackOptions(maxTime=last)
            mel.currentTime( first)
            mel.putenv('SHOTPREROLL', str(preroll))
            mel.putenv('SHOTSIMSTART', str(first))
            msg = "Simulation shot frame range set to %d-%d (%d Preroll frames)"%(first, last, preroll)
            om.MGlobal.displayInfo(msg)
    else:
        msg = "Couldn't find shot frame range information, SHOTFRAMES and/or SHOTHANDLES are missing. Please run Set Globals tp update shot information."
        om.MGlobal.displayError(msg)
        mel.confirmDialog(title='Set SIM Range ...', message=msg, button=['Ok'], defaultButton='Ok')
        return False

    return True

def set_sim_range():
    '''
    Set scene time range to simulation  range

    Parameters
    ----------

    Returns
    ---------
    bool
        True if all went ok
    '''
    #  Job ID :
    if not mc.objExists( 'defaultRenderGlobals.nim_jobID' ) :
        P.error("Maya scene doesn't have publishing info. Has this scene been published?")
        return False
    jobid = int(mc.getAttr( 'defaultRenderGlobals.nim_jobID' ))
    jobglobals = Utl.getShowGlobals( jobid )

    # Shot
    # Set frame range. Check if frame range is actually y bigger in any of sides,
    # start or end
    shotid = int(mc.getAttr( 'defaultRenderGlobals.nim_shotID' )) if mc.getAttr( 'defaultRenderGlobals.nim_class' ) == 'SHOT' else int(mc.getAttr( 'defaultRenderGlobals.nim_assetID' ))
    frames  = int(mel.getenv('SHOTFRAMES'))
    handles = int(mel.getenv('SHOTHANDLES'))
    if frames:
        preroll = int(mel.getenv('SHOTPREROLL'))
        if preroll:
            stash_frame_range()
            first = 1001 # We always start at 1001 by convention
            last = 1001 + frames - 1
            first = first - preroll
            mc.playbackOptions(ast=first)
            mc.playbackOptions(aet=last)
            mc.playbackOptions(minTime=first)
            mc.playbackOptions(maxTime=last)
            mel.currentTime( first)
            mel.putenv('SHOTSIMSTART', str(first))
            msg = "Simulation shot frame range set to %d-%d (%d Preroll frames)"%(first, last, preroll)
            om.MGlobal.displayInfo(msg)
        else:
            msg = "This scene doesnt have a Pre-Roll defined. Please use Set Sim Preroll first."
            om.MGlobal.displayError(msg)
            return False
    else:
        msg = "Couldn't find shot frame range information, SHOTFRAMES and/or SHOTHANDLES are missing. Please run Set Globals tp update shot information."
        om.MGlobal.displayError(msg)
        mel.confirmDialog(title='Set SIM Range ...', message=msg, button=['Ok'], defaultButton='Ok')
        return False

    return True


def restore_range():
    '''
    Restore previous stashed range

    Parameters
    ----------

    Returns
    ---------
    bool
        True if all went ok
    '''
    # Set frame range using stached values in envvars.
    first    = int(mel.getenv('SHOTSTART_STASH'))
    last     = int(mel.getenv('SHOTEND_STASH'))
    firstcut = int(mel.getenv('SHOTSTARTCUT_STASH'))
    lastcut  = int(mel.getenv('SHOTENDCUT_STASH'))
    if first or last or firstcut or lastcut:
        stash_frame_range()
        mc.playbackOptions(ast=firstcut)
        mc.playbackOptions(aet=lastcut)
        mc.playbackOptions(minTime=first)
        mc.playbackOptions(maxTime=last)
        mel.currentTime( firstcut)
        msg = "Frame range restored to %d-%d "%(first, last)
        om.MGlobal.displayInfo(msg)
    else:
        msg = "Couldn't find previous frame range state"
        om.MGlobal.displayError(msg)
        return False

    return True


def rtShowScriptPubInfo():
    '''
    Show scene publishing info
    '''
    mel.select('defaultRenderGlobals')

def rtCopyScenePathToClipboard():
    """Copy current scene path to clipboard"""
    from PySide2 import QtGui as QtGui2
    path = mel.file(q=True, sn=True)
    if platform.system() == 'Windows':
        if path.startswith('/') or path.startswith('\\'):
            path = "C:" + path
        path.replace('/', '\\')
    else:
        path = Utl.toPosix(path)
    cb = QtGui2.QGuiApplication.clipboard()
    cb.clear(mode=cb.Clipboard )
    cb.setText(path, mode=cb.Clipboard)

    P.info("Script path copied to clipboard: %s"%path)

def rtSetGlobals( ):
    '''
    Wrapper to call set_globals() fro the Menu

    Get globals parameters for the show and shot and apply them to our scene
    Globals are gather from environment variables and/or NIM.

    Returns
    ---------
    bool
        True if all went ok
    '''
    P.info ( 'Set Scene Globals' )
    set_globals()

    pass

def rtSetShotRange ( ):
    '''
    Wrapper to call set_shot_range() from the Menu

    Get globals parameters for the show and shot and apply them to our scene
    Globals are gather from environment variables and/or NIM.

    Returns
    ---------
    bool
        True if all went ok
    '''
    P.info ( 'Set Shot Range' )
    set_shot_range()

    pass

def rtSetPreRoll( ):
    '''
    Set pre roll frames for simulations

    Returns
    ---------
    bool
        True if all went ok
    '''
    P.info ( 'Set Pre-Roll' )
    set_preroll()

    pass

def rtSimRange( ):
    '''
    Set simulation range in timeline

    Returns
    ---------
    bool
        True if all went ok
    '''
    P.info ( 'Set Sim Range' )
    set_sim_range()

    pass

def rtRestoreRange( ):
    '''
    Restore previously stached range

    Returns
    ---------
    bool
        True if all went ok
    '''
    P.info ( 'Restore Range' )
    restore_range()

    pass

def rtCreateTaskForScript():
    '''
    Create an appropriate task in the shot/asset for this user according with the task used by the script filename
    
    Returns
    -------
    bool
        True if task was created correctly or if it already exists. False if task creation failed
    '''
    path = mel.file(q=True, sn=True)
    task = Rt.pubTask( filepath=path, user=Api.get_user())
    if task:
        #  Task ID :
        if not mc.attributeQuery( 'nim_taskID', node='defaultRenderGlobals', exists=True) :
            mc.addAttr( 'defaultRenderGlobals', longName='nim_taskID', dt="string")
        mc.setAttr( 'defaultRenderGlobals.nim_taskID', lock=False)
        mc.setAttr( 'defaultRenderGlobals.nim_taskID', str(task['taskID']), type='string' )
        mc.setAttr( 'defaultRenderGlobals.nim_taskID', lock=True, keyable=False)
    else:
        return False
    return  True

def rtCopySceneFileID( ):
    '''
    Copy Scene file NIM's FilE ID to the clipboard

    Returns
    ---------
    bool
        True if all went ok
    '''
    #  Job ID :
    if not mc.objExists( 'defaultRenderGlobals.nim_jobID' ) :
        P.error("Maya scene doesn't have publishing info. Has this scene been published?")
        return False
    jobid = int(mc.getAttr( 'defaultRenderGlobals.nim_jobID' ))
    jobglobals = Utl.getShowGlobals( jobid )
    P.info( 'Copy Hip File ID to Clipboard' )
    fileid  = str(int(mc.getAttr( 'defaultRenderGlobals.nim_fileID' )))
    from PySide2 import QtGui as QtGui2
    cb = QtGui2.QGuiApplication.clipboard()
    cb.clear(mode=cb.Clipboard )
    cb.setText(fileid, mode=cb.Clipboard)
    
    P.info("Hip File ID copied to the clipboard: %s"%fileid)

    pass

def rtCopySceneFileID( ):
    '''
    Copy Scene file NIM's FilE ID to the clipboard

    Returns
    ---------
    bool
        True if all went ok
    '''
    pass

def rtPublishFlipbook( ):
    '''
    Publish current flipbook in MPlay

    Returns
    ---------
    bool
        True if all went ok
    '''
    P.info("Publish Flipbook")
    pipe.publish_flipbook()

    pass


def rtOpenScene():
    '''
    Function to be called from a script node when a scene is opened.

    Parameters
    ----------
    

    Returns
    ---------
    bool
        True if all commands executed correctly.

    '''
    pipe.sentinel_start()

    pass


def rtDebugSentinel( menuitem):
    '''
    Toggle envvar to enable/disable of sentinel process logging

    Parameters
    ----------

    Returns
    ---------
    bool
        True if all commands executed correctly.

    '''
    toggle = mc.menuItem(menuitem, query=True, checkBox=True)
    mel.putenv('RT_SENTINEL_VERBOSE', str(int(toggle)))
    P.info("%s sentinel process debug"%('Disable', 'Enable')[int(toggle)])

    pass




def makeProject(projectLocation='', renderPath='') :
    'Create the new project and workspace setup'

    createDirectories = True

    # Get list of all standard file rules
    fileRules = mm.eval('np_getDefaultFileRuleWidgets')
    try:
        #Update with NIM Render Directory
        if renderPath:
            imageRuleIndex=fileRules.index('images'.replace('\\','/'))
            fileRules[imageRuleIndex+1]=str(renderPath)
    except:
        P.error('Could not set NIM render path in workspace.')

    mc.workspace( projectLocation, openWorkspace=True )

    if createDirectories :
        print("Creating Directories");
        # Set workspace current directory to the workspace root so relative paths created with -create are located correctly
        mc.workspace( dir=mc.workspace(q=True,rootDirectory=True) )

    items=len(fileRules)
    for i in range(0 ,items-1, 2) :
        # each rule has 2 entries: rulename, value
        ruleName  = fileRules[i]
        ruleValue = fileRules[i+1]
        mc.workspace(fr=(ruleName,ruleValue))
        if createDirectories :
            mc.workspace(create=ruleValue)

    #Adding images folder to project
    mc.workspace(create='images')

    mc.workspace(saveWorkspace=True)
    mc.workspace(projectLocation,o=True)
    mm.eval('if (`window -ex projectWindow`){print "Window Open"; deleteUI projectWindow;projectWindow;}')
    mm.eval('np_resetBrowserPrefs;');

    return True


class Pub_Chex( QtGui.QWidget ) :
    
    def __init__( self, parent=None, nim=None ) :
        super(Pub_Chex, self).__init__(parent)
        self.setWindowTitle( 'Maya Publish Checks' )
        
        #  Widgets :
        
        #  Check Boxes :
        self.delUnselected=QtGui.QCheckBox()
        self.applyShaders=QtGui.QCheckBox()
        self.delUnusedShaders=QtGui.QCheckBox()
        self.delHist=QtGui.QCheckBox()
        #self.delNonDeformerHist=QtGui.QCheckBox()
        #  Set check boxes :
        self.delUnusedShaders.setChecked( True )
        self.delHist.setChecked( True )
        #  Store all check boxes :
        self.checkBoxes=[self.delUnselected, self.applyShaders,
            self.delUnusedShaders, self.delHist]
        
        #  Combo Boxes :
        self.delDeformers=QtGui.QComboBox()
        self.delConns=QtGui.QComboBox()
        self.delCurves=QtGui.QComboBox()
        self.delLocs=QtGui.QComboBox()
        self.delCams=QtGui.QComboBox()
        self.delIPlanes=QtGui.QComboBox()
        self.delLights=QtGui.QComboBox()
        self.delDispLayers=QtGui.QComboBox()
        self.delRenLayers=QtGui.QComboBox()
        #  Store all combo boxes :
        self.comboBoxes=[self.delDeformers, self.delConns, self.delCurves, self.delLocs,
            self.delCams, self.delIPlanes, self.delLights, self.delDispLayers, self.delRenLayers]
        #  Populate combo boxes :
        for comboBox in self.comboBoxes :
            comboBox.addItems( ['All', 'Unselected', 'None'] )
        
        #  Buttons :
        self.btn_sel=QtGui.QPushButton('Select All')
        self.btn_unsel=QtGui.QPushButton('Select None')
        self.btn_1=QtGui.QPushButton('Run Checks + Publish')
        self.btn_2=QtGui.QPushButton('Run Checks ONLY')
        #  Button Layouts :
        self.selBtnLayout=QtGui.QHBoxLayout()
        self.selBtnLayout.addWidget( self.btn_sel )
        self.selBtnLayout.addWidget( self.btn_unsel )
        self.btnLayout=QtGui.QHBoxLayout()
        self.btnLayout.addWidget( self.btn_1 )
        self.btnLayout.addWidget( self.btn_2 )
        
        #  Form Layout :
        self.form_layout=QtGui.QFormLayout()
        #  Add check boxes to layout :
        self.form_layout.addRow( 'Delete Un-selected Geometry:', self.delUnselected )
        self.form_layout.addRow( 'Delete Un-used Shaders:', self.delUnusedShaders )
        self.form_layout.addRow( 'Apply Default Shader:', self.applyShaders )
        self.form_layout.addRow( 'Delete History:', self.delHist )
        #  Add combo boxes to layout :
        self.form_layout.addRow( 'Delete Deformers:', self.delDeformers )
        self.form_layout.addRow( 'Delete Constraints:', self.delConns )
        self.form_layout.addRow( 'Delete Curves:', self.delCurves )
        self.form_layout.addRow( 'Delete Locators:', self.delLocs )
        self.form_layout.addRow( 'Delete Camers:', self.delCams )
        self.form_layout.addRow( 'Delete Image Planes:', self.delIPlanes )
        self.form_layout.addRow( 'Delete Lights:', self.delLights )
        self.form_layout.addRow( 'Delete Display Layers:', self.delDispLayers )
        self.form_layout.addRow( 'Delete Render Layers:', self.delRenLayers )
        
        #  Main Layout :
        self.layout=QtGui.QVBoxLayout( self )
        self.layout.addLayout( self.form_layout )
        self.layout.addLayout( self.selBtnLayout )
        self.layout.addLayout( self.btnLayout )
        
        #  Connections :
        self.btn_sel.clicked.connect( self.sel )
        self.btn_unsel.clicked.connect( self.unsel )
        self.btn_1.clicked.connect( lambda: self.run_checks( nim=nim, pub=True ) )
        self.btn_2.clicked.connect( lambda: self.run_checks( nim=nim, pub=False ) )
        
        #  Show the Window :
        self.show()
        
        return
    
    
    def sel(self) :
        'Turns on all check and combo boxes.'
        #  Set Check Boxes :
        for cb in self.checkBoxes :
            cb.setChecked( True )
        #  Set Combo Boxes :
        for cb in self.comboBoxes :
            cb.setCurrentIndex( 0 )
        return
    
    
    def unsel(self) :
        'Turns off all check and combo boxes.'
        #  Set Check Boxes :
        for cb in self.checkBoxes :
            cb.setChecked( False )
        #  Set Combo Boxes :
        for cb in self.comboBoxes :
            cb.setCurrentIndex( 2 )
        return
    
    
    def run_checks( self, pub=False, nim=None) :
        'Runs the checks with the values from the publish check window'
        
        #  Run publishing checks :
        self.pub_check()
        '''
            del_unselected=self.delUnselected,
            del_unusedShaders=self.delUnusedShaders, applyDefaultShaders=self.applyShaders,
            del_hist=self.delHist, deformer_opt=self.delDeformers.currentText(),
            conn_opt=self.delConns.currentText(), curves_opt=self.delCurves.currentText(),
            loc_opt=self.delLocs, cam_opt=self.delCams.currentText(),
            ip_opt=self.delIPlanes.currentText(), light_opt=self.delLights.currentText(),
            dl_opt=self.delDispLayers.currentText(), rl_opt=self.delRenLayers.currentText() )
        '''
        #  Version Up, Publish and Close the Window, if specified :
        if pub :
            if not nim :
                nim=Nim.NIM()
            Api.versionUp( nim=self.nim, win_launch=False, pub=True )
            self.close()
        
        return
    
    
    def pub_check(self) :
        'Cleans up a Maya file before publishing'
        
        #  Selection :
        sel=mc.ls( sl=True, int=True, transforms=True )
        #  Select entire hierarchy :
        if sel :
            hier=mc.listRelatives( sel, children=True, allDescendents=True, type='transform',
                fullPath=True )
            if hier :
                sel.extend( hier )
        
        
        #  Variables :
        #===------------
        
        non_linears=['deformBend','deformFlare','deformSine','deformSquash','deformTwist','deformWave']
        constraints=['pointConstraint', 'aimConstraint', 'orientConstraint', 'scaleConstraint', 'parentConstraint', \
            'geometryConstraint', 'normalConstraint', 'tangentConstraint', 'pointOnPolyConstraint']
        mayaLights=['ambientLight', 'directionalLight', 'areaLight', 'pointLight', 'spotLight', 'volumeLight']
        vrayLights=['VRayLightSphereShape', 'VRayLightDomeShape', 'VRayLightRectShape', 'VRayLightIESShape']
        
        
        #  Delete :
        #===-------
        
        #  Delete Unselected Geometry :
        if self.delUnselected.isChecked() :
            P.info('Deleting unselected geometry...')
            delGeo=[]
            objs=sel[:]
            allGeo=mc.listRelatives( mc.ls( geometry=True ), parent=True, fullPath=True )
            for obj in sel :
                prnts=mc.listRelatives( obj, allParents=True, fullPath=True )
                if prnts :
                    prnt=prnts[0]
                    while prnts :
                        objs.extend( prnts )
                        prnts=mc.listRelatives( prnt, allParents=True, fullPath=True )
                        if prnts : prnt=prnts[0]
            delGeo=[x for x in allGeo if x not in objs]
            mc.delete( delGeo )
            P.info('    Unselected geometry deleted successfully.')
        
        #  Apply Default Shader :
        if self.applyShaders.isChecked() :
            P.info('Applying default shaders...')
            mc.select( all=True )
            mm.eval( 'hyperShade -assign initialShadingGroup' )
            mc.select( sel, replace=True )
            P.info('    Default shaders applied successfully.')
        
        #  Delete Unused Shaders :
        if self.delUnusedShaders.isChecked() :
            P.info('Deleting unused shaders...')
            mm.eval( 'hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes")' )
            P.info('    Unused shaders have been deleted successfully.')
        
        #  Delete history :
        if self.delHist.isChecked() :
            P.info( 'Deleteing all history...' )
            mm.eval( 'DeleteAllHistory' )
            P.info('    All history deleted successfully.')
        
        
        #  Clean File :
        #===-------------
        
        #  Delete Deformers :
        
        if self.delDeformers.currentText()=='All' :
            P.info( 'Deleting all deformers...' )
            #  FFD's :
            P.info('    Deleting FFDs...')
            try : mc.delete( mc.ls( type='ffd' ) )
            except : P.info('      No FFDs found.')
            #  Lattices :
            P.info( '    Deleting Latices...' )
            try : mc.delete( mc.ls( type='lattice' ) )
            except : P.info('      No Lattices found.')
            #  Clusters :
            P.info('    Deleting clusters...')
            try : mc.delete( mc.ls( type='cluster' ) )
            except : P.info('      No Clusters found.')
            #  Sculpt Deformers :
            P.info('    Deleting Sculpts...')
            try : mm.eval('DeleteAllSculptObjects')
            except : P.info('      No Sculpts found.')
            #  Non-Linear Deformers :
            P.info('    Deleting non-linear deformers...')
            try : mm.eval('DeleteAllNonLinearDeformers')
            except : P.info('      No non-linear deformers found.')
            #  Wire Defomers :
            P.info('    Deleting Wires...')
            try :mc.delete( mc.ls( type='wire' ) )
            except : P.info('      No Wires found.')
        elif self.delDeformers.currentText()=='Unselected' :
            delDeformers=[]
            deformers=['lattice','cluster','wire']
            for deformer in deformers :
                obj_deformers=mc.ls( type=deformer, int=True )
                if obj_deformers :
                    for obj_deformer in obj_deformers :
                        if deformer=='lattice' :
                            allDeformers=mc.listRelatives( obj_deformer, parent=True, type='transform',
                                fullPath=True )
                            if allDeformers :
                                for obj in allDeformers :
                                    if obj not in sel :
                                        delDeformers.append( obj )
                        elif deformer=='cluster' :
                            connections=mc.listConnections( obj_deformer, type='transform' )
                            for conn in connections :
                                cls_long=mc.ls( conn, int=True )
                                if cls_long :
                                    if cls_long[0] not in sel :
                                        delDeformers.append( obj_deformer )
                        else :
                            if obj_deformer not in sel :
                                delDeformers.append( obj_deformer )
            if delDeformers :
                mc.delete( delDeformers )
            
            '''
            P.info('    Deleteing Un-selected Deformers...')
            for deformer in deformers :
                try :
                    mc.select( mc.ls( type=deformer ) )
                    for obj in sel :
                        mc.select( obj, d=True )
                    mc.select( mc.ls( transforms=True, sl=True ) )
                    mc.delete()
                except : P.info( '  No un-sel deformers found' )
            #  Try deleting un-necessary implicit spheres :
            try :
                mc.select( mc.ls( type='implicitSphere' ) )
                for select in sel :
                    mc.select( select, d=True )
                    mc.select( mc.ls( transforms=True, sl=True ) )
                    P.info( 'Deleting un-necessary implicit spheres...' )
                    mc.delete()
            except : P.info( '  No un-sel implicit spheres found' )
            #  Try deleting non-linears :
            try :
                for non_linear in non_linears :
                    mc.select( mc.ls( type=non_linear ) )
                    for select in sel :
                        mc.select( select, d=True )
                    mc.select( mc.ls( transforms=True, sl=True ) )
                    P.info( 'Deleting un-necessary non-linears...' )
                    mc.delete()
            except : P.info( '  No un-sel non-linears found' )
        
        #  Delete Constraints :
        if conn_opt=='All' :
            P.info( 'Deleteing all constraints....' )
            mm.eval('DeleteAllConstraints')
        elif conn_opt=='Unsel' :
            P.info( 'Deleting un-sel constraints....' )
            try :
                for constraint in constraints :
                    mc.select( mc.ls( type=constraint ) )
                    for select in sel :
                        mc.select( select, d=True )
                    mc.select( mc.ls( transforms=True, sl=True ) )
                    mc.delete()
            except :
                P.info( '  No constraints found' )
        
        #  Delete Curves :
        if curves_opt=='All' :
            try :
                mc.select( mc.ls( type='nurbsCurve' ) )
                mc.select( mc.ls( type='bezierCurve' ), add=True )
                mc.select( ms.ls( transforms=True, sl=True) )
                P.info( 'Deleteing all curves....' )
                mc.delete()
            except :
                P.info( '  No curves found' )
        elif curves_opt=='Unsel' :
            try :
                mc.select( mc.ls( type='nurbsCurve' ) )
                mc.select( mc.ls( type='bezierCurve' ), add=True )
                for select in sel :
                    mc.select( select, d=True )
                mc.select( mc.ls( transforms=True, sl=True ) )
                P.info( 'Deleting un-sel curves....' )
                mc.delete()
            except :
                P.info( '  No curves found' )
        
        #  Delete Locators :
        #TO DO -> Make sure locators don't have any connections.
        if loc_opt=='All' :
            try :
                mc.select( mc.ls( type='locator' ) )
                mc.select( ms.ls( transforms=True, sl=True ) )
                P.info( 'Deleteing all locators....' )
                mc.delete()
            except :
                P.info( '  No Locators Found' )
        elif loc_opt=='Unsel' :
            try :
                mc.select( mc.ls( type='locator' ) )
                for select in sel :
                    mc.select( select, d=True )
                mc.select( mc.ls( transforms=True, sl=True ) )
                P.info( 'Deleting un-sel locators....' )
                mc.delete()
            except :
                P.info( '  No locators found' )
        
        #  Delete Cameras :
        if cam_opt=='All' :
            P.info( 'Deleteing all cameras....' )
            mm.eval( 'DeleteAllCameras' )
        elif cam_opt=='Unsel' :
            try :
                mc.select( mc.ls( type='camera' ) )
                for select in sel :
                    mc.select( select, d=True )
                mc.select( mc.ls( transforms=True, sl=True ) )
                P.info( 'Deleting un-sel cameras....' )
                mc.delete()
            except :
                P.info( '  No cameras found' )
        
        #  Delete Imageplanes :
        if ip_opt=='All' :
            P.info( 'Deleteing all ImagePlanes....' )
            mm.eval( 'DeleteAllImagePlanes' )
        elif ip_opt=='Unsel' :
            try :
                mc.select( mc.ls( type='imagePlane' ) )
                for select in sel :
                    mc.select( select, d=True )
                mc.select( mc.ls( transforms=True, sl=True ) )
                P.info( 'Deleting un-sel ImagePlanes....' )
                mc.delete()
            except :
                P.info('  No ImagePlanes found')
            
        #  Delete Lights :
        if light_opt=='All' :
            P.info( 'Deleteing all lights....' )
            mm.eval( 'DeleteAllLights' )
            for vrayLight in vrayLights :
                try :
                    mc.select( mc.ls( type=vrayLight ) )		    
                    mc.select( mc.ls( transforms=True, sl=True ) )
                    P.info( 'Deleting VRay lights...' )
                    mc.delete()
                except :
                    P.info( '  No '+vrayLight+' found' )
        elif light_opt=='Unsel' :
            P.info( 'Deleting un-sel lights....' )
            #  Delete Maya Lights :
            for mayaLight in mayaLights :
                try :
                    mc.select( mc.ls( type=mayaLight ) )
                    for select in sel :
                        mc.select( select, d=True )
                    mc.select( mc.ls( transforms=True, sl=True ) )
                    P.info( '  Deleting Maya lights...' )
                    mc.delete()
                except :
                    P.info( '    No '+mayaLight+' found' )
            #  Delete VRay Lights :
            for vrayLight in vrayLights :
                try :
                    mc.select( mc.ls( type=vrayLight ) )
                    for select in sel :
                        mc.select( select, d=True )
                    mc.select( mc.ls( transforms=True, sl=True ) )
                    P.info( 'Deleting VRay lights...' )
                    mc.delete()
                except :
                    P.info( '  No '+vrayLight+' found' )
        
        #  Delete Display Layers :
        if dl_opt=='All' :
            try :
                mc.select( mc.ls( type='displayLayer' ) )
                P.info( 'Deleteing all display layers....' )
                mc.delete()
            except :
                P.info( '  No display layers found' )
        elif dl_opt=='Unsel' :
            try :
                mc.select( mc.ls( type='displayLayer' ) )
                for select in sel :
                    mc.select( select, d=True )
                mc.select( mc.ls( transforms=True, sl=True ) )
                P.info( 'Deleting un-sel display layers....' )
                mc.delete()
            except :
                P.info( '  No display layers found' )
        
        #  Delete Render Layers :
        if rl_opt=='All' :
            try :
                mc.select( mc.ls( type='renderLayer' ) )
                P.info( 'Deleteing all render layers....' )
                mc.delete()
            except :
                P.info( '  No render layers found' )
        elif rl_opt=='Unsel' :
            try :
                mc.select( mc.ls( type='renderLayer' ) )
                for select in sel :
                    mc.select( select, d=True )
                mc.select( mc.ls( transforms=True, sl=True ) )
                P.info( 'Deleting un-sel render layers....' )
                mc.delete()
            except:
                P.info( '  No render layers found' )
        
        #  Delete empty group nodes ?
        '''
        P.info( '\n\nThe file is clean!\n' )
        
        return


#  End of Class


#  Fix for Maya Shift loosing focus
class MainWindow(QtGui.QMainWindow):
    def keyPressEvent(self, event):
        """Override keyPressEvent to keep focus on QWidget in Maya."""
        if (event.modifiers() & QtCore.Qt.ShiftModifier):
            self.shift = True
            pass # make silent

from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
class UIUtils(MayaQWidgetBaseMixin, QtGui.QWidget):
    """Base class for UI constructors."""

    def window(self):
        """Defines basic window parameters."""
        parent = self.get_maya_window()
        window = MainWindow(parent)

        return window

    def get_maya_window(self):
        """Grabs the Maya window."""
        pointer = mui.MQtUtil.mainWindow()
        return shiboken.wrapInstance(int(pointer), QtGui.QWidget)


#  End

