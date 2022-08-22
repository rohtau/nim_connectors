#!/bin/env python
#******************************************************************************
#
# Filename:    exportHook.py
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
import os,sys,re
from pprint import pprint, pformat

# NIM imports
import nim_core.nim_print        as nimP
import nim_core.nim              as Nim
import nim_core.nim_file         as nimF
import nim_core.nim_api          as nimAPI
import nim_core.nim_rohtau       as nimRt
import nim_core.nim_rohtau_utils as nimUtl
from nim_core import padding 

#  Import Python GUI packages :
try : 
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
except ImportError :
    try : 
        from PySide.QtGui import *
        from PySide.QtCore import *
    except ImportError : 
        print("NIM: Failed to load UI Modules")

# Flame
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


# print ("NIM Script Path: %s" % nimScriptPath)
# print ("NIM Python Path: %s" % nimFlamePythonPath)
# print ("NIM Preset Path: %s" % nimFlamePresetPath)


# If relocating these scripts uncomment the line below and enter the fixed path
# to the NIM Connector Root directory
#
# nimScriptPath = [NIM_CONNECTOR_ROOT]
#

sys.path.append(nimScriptPath)

import nimFlameExport
import rtFlameExport

debug = False

# Hooks in this files are called in the following order:
#
# preCustomExport (optional depending on getCustomExportProfiles)
#  preExport
#   preExportSequence
#    preExportAsset
#    postExportAsset  (could be done in backburner depending of useBackburnerPostExportAsset)
#    ...
#   postExportSequence
#   ...
#  postExport
# postCustomExport (optional depending on getCustomExportProfiles)

# Hook called before a custom export begins. This can be used to fill
# information that would have normally been extracted from the export window.
#
# info [Dictionary] [Modifiable]
#    Information about the export,
#
#    Keys:
#
#    destinationHost: [String] [Modifiable]
#       Host name where the exported files will be written to.
#       Defaults to localhost.
#
#    destinationPath: [String] [Modifiable]
#       Export path root.
#       Defaults to /tmp
#
#    presetPath: [String] [Modifiable]
#       Path to the preset used for the export.
#       Most be defined by this method.
#
#    useTopVideoTrack: [Boolean] [Modifiable]
#       Use only the top video track and ignore the other ones.
#       (False if not defined)
#
#    exportBetweenMarks: [Boolean] [Modifiable]
#       Export between the In  and Out marks, excluding the marked frames.
#       If there is no In, export from start of sequence to Out;
#       if there is no Out, export from the In to the end of the sequence.
#       (False if not defined)
#
#    isBackground: [Boolean] [Modifiable]
#       Perform the export in background.
#       (True if not defined)
#
#    abort: [Boolean] [Modifiable]
#       Hook can set this to True if the custom export process should be
#       aborted.
#
#    abortMessage: [String] [Modifiable]
#       Error message to be displayed to the user when the export process has
#       been aborted
#
# userData [Object] [Modifiable]
#   Object that could have been populated by previous export hooks and that
#   will be carried over into the subsequent export hooks.
#   This can be used by the hook to pass black box data around.
#   This will usually be a dictionary.
#   The object can be modified but not reassigned.
#
def pre_custom_export(info, userData, *args, **kwargs):
    print("pre_custom_export - start >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    if debug :
        print(info)
        print(userData)
    
    #Test what 'exportType' was select in the UI, by the user
    
    #NimExportSequence
    if userData['nim_export_type'] == 'NimExportSequence' :
        #Set the proper 'presetPath' in the info dictionary
        #This defines which preset is used for the custom encode job
        #info['presetPath'] = '/path/to/export/presets/uncompressed_qt.xml'
        
        print("NIM - Exporting Sequence")
        userData['nim_export_sequence'] = True
        
        exportDlg = nimFlameExport.NimExportSequenceDialog()
        exportDlg.show()
        if exportDlg.exec_() :
            nimP.info("Export dialog settings:")

            nimP.info("User ID: %s" % exportDlg.nim_userID)
            userData['nim_userID'] = exportDlg.nim_userID
            
            nimP.info("Server ID: %s" % exportDlg.nim_serverID)
            userData['nim_serverID'] = exportDlg.nim_serverID
            
            nimP.info("Server OS Path: %s" % exportDlg.nim_serverOSPath)
            nim_serverOSPath = exportDlg.nim_serverOSPath
            userData['nim_serverOSPath'] = nim_serverOSPath
            
            # Set destination path to NIM server path
            nimP.info("Destination Path: %s" % info['destinationPath'])
            info['destinationPath'] = nim_serverOSPath
            
            
            nimP.info("Job ID: %s" % exportDlg.nim_jobID)
            userData['nim_jobID'] = exportDlg.nim_jobID
            
            nimP.info("Show ID: %s" % exportDlg.nim_showID)
            userData['nim_showID'] = exportDlg.nim_showID
            
            nimP.info("Video Element ID: %s" % exportDlg.videoElementID)
            userData['videoElementID'] = exportDlg.videoElementID
            
            nimP.info("Audio Element ID: %s" % exportDlg.audioElementID)
            userData['audioElementID'] = exportDlg.audioElementID
            
            nimP.info("Open Clip Element ID: %s" % exportDlg.openClipElementID)
            userData['openClipElementID'] = exportDlg.openClipElementID
            
            nimP.info("Batch Open Clip Element ID: %s" % exportDlg.batchOpenClipElementID)
            userData['batchOpenClipElementID'] = exportDlg.batchOpenClipElementID
            
            nimP.info("Batch Task Type ID: %s" % exportDlg.batchTaskTypeID)
            userData['batchTaskTypeID'] = exportDlg.batchTaskTypeID
            userData['batchTaskTypeFolder'] = exportDlg.batchTaskTypeFolder

            nimP.info("Puiblish Export: %s" % exportDlg.pub_dopub)
            userData['pub_dopub'] = exportDlg.pub_dopub
            nimP.info("Autover: %s"%exportDlg.pub_autover)
            userData['pub_autover'] = exportDlg.pub_autover
            nimP.info("Publish Version %d" % int(exportDlg.pub_ver))
            userData['pub_ver'] = exportDlg.pub_ver
            info['versionNumber'] = int(exportDlg.pub_ver)
            info['versionName'] = "v" + str(exportDlg.pub_ver).zfill(3)

            
            # Create empty dictionary for shot data
            userData['shotData'] = {}
            
            # Set NIM Preset
            nim_preset = exportDlg.nim_preset
            info['presetPath'] = nimFlamePresetPath + '/sequence/'+nim_preset+'.xml'         
            
            # Process in Background
            info['isBackground'] = False
        
        else:
            print("NIM - Canceled Export to NIM")
            userData['nim_export_sequence'] = False
            info['abort'] = True
    
    
    #NimExportEdit
    if userData['nim_export_type'] == 'NimExportEdit' :
        #Set the proper 'presetPath' in the info dictionary
        #This defines which preset is used for the custom encode job
        #info['presetPath'] = '/path/to/export/presets/uncompressed_qt.xml'
        
        print("NIM - Exporting Edit")
        userData['nim_export_edit'] = True
        
        exportDlg = nimFlameExport.NimExportEditDialog()
        exportDlg.show()
        if exportDlg.exec_() :
            print("NIM - nim_userID: %s" % exportDlg.nim_userID)
            userData['nim_userID'] = exportDlg.nim_userID
            
            print("NIM - serverID: %s" % exportDlg.nim_serverID)
            userData['nim_serverID'] = exportDlg.nim_serverID
            
            print("NIM - serverOSPath: %s" % exportDlg.nim_serverOSPath)
            nim_serverOSPath = exportDlg.nim_serverOSPath
            userData['nim_serverOSPath'] = nim_serverOSPath
            
            # Set destination path to NIM server path
            info['destinationPath'] = nim_serverOSPath
            print("Destination Path: %s" % info['destinationPath'])
            
            
            print("NIM - jobID: %s" % exportDlg.nim_jobID)
            userData['nim_jobID'] = exportDlg.nim_jobID
            
            print("NIM - showID: %s" % exportDlg.nim_showID)
            userData['nim_showID'] = exportDlg.nim_showID
            
            # Create empty dictionary for shot data
            userData['shotData'] = {}
            
            # Set NIM Preset
            nim_preset = exportDlg.nim_preset
            info['presetPath'] = nimFlamePresetPath + '/edit/'+nim_preset+'.xml'         
            
            # Process in Background
            info['isBackground'] = False
            #nim_bg_export = exportDlg.nim_bg_export
            #info['isBackground'] = nim_bg_export
           
        else:
            print("NIM - Canceled Export to NIM")
            userData['nim_export_edit'] = False
            info['abort'] = True
    
    
    #NimExportEdit
    if userData['nim_export_type'] == 'NimExportDaily' :
        #Set the proper 'presetPath' in the info dictionary
        #This defines which preset is used for the custom encode job
        #info['presetPath'] = '/path/to/export/presets/uncompressed_qt.xml'
        
        print("NIM - Exporting Daily")
        userData['nim_export_daily'] = True
        
        exportDlg = nimFlameExport.NimExportDailyDialog()
        exportDlg.show()
        if exportDlg.exec_() :
            # print("NIM - nim_userID: %s" % exportDlg.nim_userID)
            nimP.info("UserID: %s" % exportDlg.nim_userID)
            userData['nim_userID'] = exportDlg.nim_userID
            
            # print("NIM - serverID: %s" % exportDlg.nim_serverID)
            nimP.info("ServerID: %s" % exportDlg.nim_serverID)
            userData['nim_serverID'] = exportDlg.nim_serverID
            
            # print("NIM - serverOSPath: %s" % exportDlg.nim_serverOSPath)
            nimP.info("Server OS Path: %s" % exportDlg.nim_serverOSPath)
            nim_serverOSPath = exportDlg.nim_serverOSPath
            userData['nim_serverOSPath'] = nim_serverOSPath
            
            # Set destination path to NIM server path
            info['destinationPath'] = nim_serverOSPath
            # print("Destination Path: %s" % info['destinationPath'])
            nimP.info("Destination Path: %s" % info['destinationPath'])
            
            
            # print("NIM - jobID: %s" % exportDlg.nim_jobID)
            nimP.info("JobID: %s" % exportDlg.nim_jobID)
            userData['nim_jobID'] = exportDlg.nim_jobID
            
            # print("NIM - showID: %s" % exportDlg.nim_showID)
            nimP.info("ShowID: %s" % exportDlg.nim_showID)
            userData['nim_showID'] = exportDlg.nim_showID
            
            # print("NIM - shotID: %s" % exportDlg.nim_shotID)
            # userData['nim_shotID'] = exportDlg.nim_shotID
            
            # print("NIM - taskID: %s" % exportDlg.nim_taskID)
            # userData['nim_taskID'] = exportDlg.nim_taskID

            # Versioning settings
            userData['pub_autover'] = exportDlg.pub_autover
            userData['pub_ver'] = exportDlg.pub_ver
            
            # Create empty dictionary for shot data
            userData['shotData'] = {}
            
            # Set NIM Preset
            nim_preset = exportDlg.nim_preset
            info['presetPath'] = nimFlamePresetPath + '/daily/'+nim_preset+'.xml'         
            
            # Process in Background
            info['isBackground'] = False
        
        else:
            print("NIM - Canceled Export to NIM")
            nimP.warning("Canceled Conform Export")
            userData['nim_export_edit'] = False
            info['abort'] = True

    #
    # rohtau Exports
    #rohtauExportSequence
    if userData['nim_export_type'] == 'rohtauExportSequence' :
        #Set the proper 'presetPath' in the info dictionary
        #This defines which preset is used for the custom encode job
        #info['presetPath'] = '/path/to/export/presets/uncompressed_qt.xml'
        
        # print("NIM - Exporting Sequence")
        nimP.info("Exporting Sequence")
        userData['nim_export_sequence'] = True
        
        # exportDlg = nimFlameExport.NimExportSequenceDialog()
        exportDlg = rtFlameExport.rtExportSequenceDialog()
        exportDlg.show()
        if exportDlg.exec_() :
            nimP.info("Export dialog settings:")

            nimP.info("User ID: %s" % exportDlg.nim_userID)
            userData['nim_userID'] = exportDlg.nim_userID
            
            nimP.info("Server ID: %s" % exportDlg.nim_serverID)
            userData['nim_serverID'] = exportDlg.nim_serverID
            
            nimP.info("Server OS Path: %s" % exportDlg.nim_serverOSPath)
            nim_serverOSPath = exportDlg.nim_serverOSPath
            userData['nim_serverOSPath'] = nim_serverOSPath
            
            # Set destination path to NIM server path
            # nimP.info("Destination Path: %s" % info['destinationPath'])
            # info['destinationPath'] = nim_serverOSPath
            
            
            nimP.info("Job ID: %s" % exportDlg.nim_jobID)
            userData['nim_jobID'] = exportDlg.nim_jobID
            nimP.info("Job Number: %s" % exportDlg.nim_jobName)
            userData['nim_jobName'] = exportDlg.nim_jobName
            
            nimP.info("Show ID: %s" % exportDlg.nim_showID)
            userData['nim_showID'] = exportDlg.nim_showID
            
            nimP.info("Video Element ID: %s" % exportDlg.videoElementID)
            userData['videoElementID'] = exportDlg.videoElementID
            
            nimP.info("Audio Element ID: %s" % exportDlg.audioElementID)
            userData['audioElementID'] = exportDlg.audioElementID
            
            nimP.info("Open Clip Element ID: %s" % exportDlg.openClipElementID)
            userData['openClipElementID'] = exportDlg.openClipElementID
            
            nimP.info("Batch Open Clip Element ID: %s" % exportDlg.batchOpenClipElementID)
            userData['batchOpenClipElementID'] = exportDlg.batchOpenClipElementID
            
            nimP.info("Batch Task Type ID: %s" % exportDlg.batchTaskTypeID)
            userData['batchTaskTypeID'] = exportDlg.batchTaskTypeID
            userData['batchTaskTypeFolder'] = exportDlg.batchTaskTypeFolder

            # FIXME: all new parameters in the export dialog are returning empty
            # strings 
            nimP.info("Puiblish Export: %s" % exportDlg.pub_dopub)
            userData['pub_dopub'] = exportDlg.pub_dopub
            nimP.info("Autover: %s"%exportDlg.pub_autover)
            userData['pub_autover'] = exportDlg.pub_autover
            nimP.info("Publish Version %d" % int(exportDlg.pub_ver))
            userData['pub_ver'] = exportDlg.pub_ver
            info['versionNumber'] = int(exportDlg.pub_ver)
            info['versionName'] = "v" + str(exportDlg.pub_ver).zfill(3)

            
            # Create empty dictionary for shot data
            userData['shotData'] = {}
            
            # Set NIM Preset
            nim_preset = exportDlg.nim_preset
            info['presetPath'] = nimFlamePresetPath + '/sequence/'+nim_preset+'.xml'         
            
            # Process in Background
            info['isBackground'] = False
        
        else:
            print("NIM - Canceled Export to NIM")
            userData['nim_export_sequence'] = False
            info['abort'] = True
    
    #rohtauExportReview
    if userData['nim_export_type'] == 'rohtauExportReview' :
        #Set the proper 'presetPath' in the info dictionary
        #This defines which preset is used for the custom encode job
        #info['presetPath'] = '/path/to/export/presets/uncompressed_qt.xml'
        
        nimP.info("Exporting Review")
        userData['nim_export_daily'] = True
        
        exportDlg = nimFlameExport.NimExportDailyDialog()
        exportDlg.show()
        if exportDlg.exec_() :
            print("NIM - nim_userID: %s" % exportDlg.nim_userID)
            userData['nim_userID'] = exportDlg.nim_userID
            
            print("NIM - serverID: %s" % exportDlg.nim_serverID)
            userData['nim_serverID'] = exportDlg.nim_serverID
            
            print("NIM - serverOSPath: %s" % exportDlg.nim_serverOSPath)
            nim_serverOSPath = exportDlg.nim_serverOSPath
            userData['nim_serverOSPath'] = nim_serverOSPath
            
            # Set destination path to NIM server path
            info['destinationPath'] = nim_serverOSPath
            print("Destination Path: %s" % info['destinationPath'])
            
            
            print("NIM - jobID: %s" % exportDlg.nim_jobID)
            userData['nim_jobID'] = exportDlg.nim_jobID
            
            print("NIM - showID: %s" % exportDlg.nim_showID)
            userData['nim_showID'] = exportDlg.nim_showID
            
            print("NIM - shotID: %s" % exportDlg.nim_shotID)
            userData['nim_shotID'] = exportDlg.nim_shotID
            
            print("NIM - taskID: %s" % exportDlg.nim_taskID)
            userData['nim_taskID'] = exportDlg.nim_taskID
            
            # Create empty dictionary for shot data
            userData['shotData'] = {}
            
            # Set NIM Preset
            nim_preset = exportDlg.nim_preset
            info['presetPath'] = nimFlamePresetPath + '/daily/'+nim_preset+'.xml'         
            
            # Process in Background
            info['isBackground'] = False
        
        else:
            print("NIM - Canceled Export to NIM")
            userData['nim_export_edit'] = False
            info['abort'] = True



    print("pre_custom_export - end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    pass


# Hook called after a custom export ends.
#
# info [Dictionary] [Modifiable]
#    Information about the export,
#
#    Keys:
#
#    destinationHost: [String]
#       Host name where the exported files were written to.
#
#    destinationPath: [String]
#       Export path root.
#
#    presetPath: [String]
#       Path to the preset used for the export.
#
# userData [Object] [Modifiable]
#   Object that could have been populated by previous export hooks and that
#   will be carried over into the subsequent export hooks.
#   This can be used by the hook to pass black box data around.
#   This will usually be a dictionary.
#   The object can be modified but not reassigned.
#
def post_custom_export(info, userData, *args, **kwargs):
    print("post_custom_export - start >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    if debug :
        print(info)
        print(userData)
    print("post_custom_export - end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    pass


# Hook called before an export begins.
#
# info [Dictionary] [Modifiable]
#    Information about the export,
#
#    Keys:
#
#    destinationHost: [String]
#       Host name where the exported files will be written to.
#
#    destinationPath: [String]
#       Export path root.
#
#    presetPath: [String]
#       Path to the preset used for the export.
#
#    abort: [Boolean] [Modifiable]
#       Hook can set this to True if the export process should be aborted.
#
#    abortMessage: [String] [Modifiable]
#       Error message to be displayed to the user when the export process has
#       been aborted
#
# userData [Object] [Modifiable]
#   Object that could have been populated by previous export hooks and that
#   will be carried over into the subsequent export hooks.
#   This can be used by the hook to pass black box data around.
#   This will usually be a dictionary.
#   The object can be modified but not reassigned.
#
def pre_export(info, userData, *args, **kwargs):
    print("pre_export - start >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    if debug :
        pprint(info)
        pprint(userData)
    print("pre_export - end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    pass


# Hook called after an export ends.
#
# info [Dictionary] [Modifiable]
#    Information about the export,
#
#    Keys:
#
#    destinationHost: [String]
#       Host name where the exported files were written to.
#
#    destinationPath: [String]
#       Export path root.
#
#    presetPath: [String]
#       Path to the preset used for the export.
#
# userData [Object] [Modifiable]
#   Object that could have been populated by previous export hooks.
#   This can be used by the hook to pass black box data around.
#   This will usually be a dictionary.
#   The object can be modified but not reassigned.
#
def post_export(info, userData, *args, **kwargs):
    print("post_export - start >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    if debug :
        print(info)
        print(userData)
    print("post_export - end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    pass


# Hook called before a sequence export begins.
#
# info [Dictionary] [Modifiable]
#    Information about the export,
#
#    Keys:
#
#    destinationHost: [String]
#       Host name where the exported files will be written to.
#
#    destinationPath: [String]
#       Export path root.
#
#    sequenceName: [String]
#       Name of the exported sequence.
#
#    shotNames: [String]
#       Tuple of all shot names in the exported sequence. Multiple segments
#       could have the same shot name.
#
#    thumbnailFrameNb: [Int]
#       Frame index of the active thumnbnail
#
#    abort: [Boolean] [Modifiable]
#       Hook can set this to True if the export sequence process should
#       be aborted. If other sequences are exported in the same export session
#       they will still be exported even if this export sequence is aborted.
#
#    abortMessage: [String] [Modifiable]
#       Error message to be displayed to the user when the export sequence
#       process has been aborted
#
# userData [Object] [Modifiable]
#   Object that could have been populated by previous export hooks and that
#   will be carried over into the subsequent export hooks.
#   This can be used by the hook to pass black box data around.
#   This will usually be a dictionary.
#   The object can be modified but not reassigned.
#
def pre_export_sequence(info, userData, *args, **kwargs):
    print("pre_export_sequence - start >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    
    if debug :
        pprint(info)
        pprint(userData)
    
    # Check if Custom NIM export or Standard Export
    # If standard export then ask for NIM association
    nimShowDialog = False
    
    print("pre_export_sequence - end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    pass


# Hook called after a sequence export ends.
#
# info [Dictionary] [Modifiable]
#    Information about the export,
#
#    Keys:
#
#    destinationHost: [String]
#       Host name where the exported files were written to.
#
#    destinationPath: [String]
#       Export path root.
#
#    sequenceName: [String]
#       Name of the exported sequence.
#
#    shotNames: [String]
#       Tuple of all shot names in the exported sequence. Multiple segment
#       could have the same shot name.
#
#    thumbnailFrameNb: [Int]
#       Frame index of the active thumnbnail
#
# userData [Object] [Modifiable]
#   Object that could have been populated by previous export hooks and that
#   will be carried over into the subsequent export hooks.
#   This can be used by the hook to pass black box data around.
#   This will usually be a dictionary.
#   The object can be modified but not reassigned.
#
def post_export_sequence(info, userData, *args, **kwargs):
    print("post_export_sequence - start >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    if debug :
        print(info)
        print(userData)
    
    if 'nim_export_sequence' in userData :
        if userData['nim_export_sequence'] == True :
            shotData = userData['shotData']
        
            for shotName in shotData :
                print("shotName: %s" % shotName)
                for assetType in shotData[shotName] :
                   
                    # Update Icons
                    if assetType == 'video' :
                        print("Updating Shot Icon")
                        itemData = shotData[shotName]['video']
                        nim_shotID = itemData['nim_shotID']
                        nim_iconPath = itemData['nim_iconPath']
                        print("shotID: %s" % nim_shotID)
                        print("iconPath: %s" % nim_iconPath)
                        result = nimFlameExport.updateShotIcon(nim_shotID=nim_shotID, image_path=nim_iconPath)
                    
                    # Resolve keywords in Batch export_node files
                    if assetType == 'batch' :
                        print("Resolving Keywords in Batch Export Node")
                        itemData = shotData[shotName]['batch']
                        nim_shotID = itemData['nim_shotID']
                        resolvedPath = itemData['resolvedPath']
                        destinationPath = info['destinationPath']
                        batchPath = os.path.join(destinationPath,resolvedPath)
                        result = nimFlameExport.resolveBatchKeywords(nim_shotID=nim_shotID, batch_path=batchPath)
    
    
    if 'nim_export_edit' in userData :
        if userData['nim_export_edit'] == True :
            print("post_export_sequence - Edit")
            # Upload Edit
            nim_showID = None
            if 'nim_showID' in userData :
                nim_showID = userData['nim_showID']
        
            if 'editData' in userData :
                mov_path = userData['editData']['path']
                result = nimFlameExport.uploadEdit(nim_showID=nim_showID, mov_path=mov_path)
    
    if 'nim_export_daily' in userData :
        if userData['nim_export_daily'] == True :
            print("post_export_sequence - Daily")
            # Upload Daily
        
            nim_taskID = None
            if 'nim_taskID' in userData :
                nim_taskID = userData['nim_taskID']
        
            if 'dailyData' in userData :
                mov_path = userData['dailyData']['path']
                result = nimFlameExport.uploadDaily(nim_taskID=nim_taskID, mov_path=mov_path)
    
    print("post_export_sequence - end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    pass


# Hook called before an asset export begins.
#
# info [Dictionary] [Modifiable]
#    Information about the asset exported.
#
#    If the asset is a multi-channel media, the information might only apply to
#    the beauty layer.
#
#    Keys:
#
#    destinationHost: [String]
#       Host name where the exported files will be written to.
#
#    destinationPath: [String]
#       Export path root.
#
#    namePattern: [String]
#       List of optional naming tokens.
#
#    resolvedPath: [String] [Modifiable]
#       File pattern (relative to destinationPath) that will be exported
#       with all the tokens resolved.
#
#    assetName: [String]
#       Name of the exported asset.
#
#    sequenceName: [String]
#       Name of the sequence the asset is part of.
#
#    shotName: [String]
#       Name of the shot the asset is part of.
#
#    tapeName: [String]
#       Name of the tape the asset is part of.
#
#    assetType: [String]
#       Type of exported asset.
#       ('video', 'audio', 'movie,' 'batch', 'openClip', 'batchOpenClip', 'distributionPackage')
#
#    width: [Long]
#       Frame width of the exported asset.
#
#    height: [Long]
#       Frame height of the exported asset.
#
#    aspectRatio: [Double]
#       Frame aspect ratio of the exported asset.
#
#    depth: [String]
#       Frame depth of the exported asset.
#       ('8-bits', '10-bits', '12-bits', '16 fp')
#
#    scanFormat: [String]
#       Scan format of the exported asset.
#       ('FIELD_1', 'FIELD_2', 'PROGRESSIVE')
#
#    colourSpace: [String]
#       Colour space of the exported asset.
#
#    fps: [Double]
#       Frame rate of exported asset.
#
#    sequenceFps: [Double]
#       Frame rate of the sequence the asset is part of.
#
#    sourceIn: [Integer]
#       The source in point as a frame, using the asset frame rate (fps key).
#
#    sourceOut: [Integer]
#       The source out point as a frame, using the asset frame rate (fps key).
#
#    recordIn: [Integer]
#       The record in point as a frame, using the sequence frame rate
#       (sequenceFps key).
#
#    recordOut: [Integer]
#       The record out point as a frame, using the sequence frame rate
#       (sequenceFps key).
#
#    handleIn: [Integer]
#       Head as a frame, using the asset frame rate (fps key).
#
#    handleOut: [Integer]
#       Tail as a frame, using the asset frame rate (fps key).
#
#    track: [String]
#       ID of the sequence's track that contains the asset.
#
#    trackName: [String]
#       Name of the sequence's track that contains the asset.
#
#    segmentIndex: [Integer]
#       Asset index (1 based) in the track.
#
#    versionName: [String]
#       Current version name of export (Empty if unversioned).
#
#    versionNumber: [Integer]
#       Current version number of export (0 if unversioned).
#
#    useBackburner: [Boolean]
#       Use backburner to launch postExportAsset.
#
#    abort: [Boolean] [Modifiable]
#       Hook can set this to True if the custom export process should be
#       aborted.
#
#    abortMessage: [String] [Modifiable]
#       Error message to be displayed to the user when the export process has
#       been aborted
#
# userData [Object] [Modifiable]
#   Object that could have been populated by previous export hooks and that
#   will be carried over into the subsequent export hooks.
#   This can be used by the hook to pass black box data around.
#   This will usually be a dictionary.
#   The object can be modified but not reassigned.
#
def pre_export_asset(info, userData, *args, **kwargs):
    # TODO: Implement publishing correctly here
    # We first  publish elements and mark them as PENDING
    # Here we call to resolveAndReserve() to get the final path and do the Up
    # Version.
    # Here we can also create the conform tasks for every shot
    # We can publish a render, pubRender() and publish renders for the conform
    # task.
    # The task wil be set as in progress
    # Do we need reviews? I prefer to add them, but it can be expensive because
    # all the export is local.
    print("pre_export_asset - start >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    if 'nim_export_sequence' in userData and  userData['nim_export_sequence']:
        if 'nim_export_type' in userData and userData['nim_export_type']== 'rohtauExportSequence' :
            # XXX: nimCreateShot is responsible of creating tyhe shot and
            # resolve the output path.
            result = rtFlameExport.nimCreateShot(userData['nim_showID'], info, userData)
            info['resolvedPath'] = result['resolvedPath']
        
            # Build Shot Array
            if info['shotName'] not in userData['shotData'] :
                userData['shotData'][info['shotName']] = {}
        
            userData['shotData'][info['shotName']][info['assetType']] = result 
            userData['currentShotID'] = result['nim_shotID']
            locskeys = ('jobPath', 'shotPath', 'platesPath', 'renderPath', 'compPath')
            for loc in locskeys:
                userData["nim_%s"%loc] = result[loc]


            path = rtFlameExport.buildOutputPath( info, userData )
            info['resolvedPath'] = path
            print("Output path")
            print(path)
            export_pub_info  = rtFlameExport.renderVersionAndPublishReserve( info, userData)
            # print ("Publish Reserve")
            # pprint(export_pub_info)
            # TODO: Add shot locations
            # if doing rohtau export:
            # get Output Path
            # if publish Reserve version

        else:
            result = nimFlameExport.nimCreateShot(nim_showID=userData['nim_showID'], info=info)
        
            info['resolvedPath'] = result['resolvedPath']
        
            # Build Shot Array
            if info['shotName'] not in userData['shotData'] :
                userData['shotData'][info['shotName']] = {}
        
            userData['shotData'][info['shotName']][info['assetType']] = result 
            userData['currentShotID'] = result['nim_shotID']


    # XXX: Just for testing force abort after publishing
    # print("Info")
    # pprint(info)
    # print("User Data")
    # pprint(userData)
    info['abort'] = True
    info['abortMessage'] = "Testing ...."
#    abort: [Boolean] [Modifiable]
#       Hook can set this to True if the custom export process should be
#       aborted.
#
#    abortMessage: [String] [Modifiable]
#       Error message to be displayed to the user when the export process has
#       been aborted


    # XXX: Temporally disable these exports
    '''
    if 'nim_export_edit' in userData :
        if userData['nim_export_edit'] == True :
            info['resolvedPath'] = nimFlameExport.nimResolvePath(nim_showID=userData['nim_showID'], keyword_string=info['resolvedPath'])


    if 'nim_export_daily' in userData :
        if userData['nim_export_daily'] == True :
            info['resolvedPath'] = nimFlameExport.nimResolvePath(nim_shotID=userData['nim_shotID'], keyword_string=info['resolvedPath'])
    '''


    if debug :
        print("destinationPath: %s" % info['destinationPath'])
        print("resolvedPath: %s" % info['resolvedPath'])
        #print "shotName: %s" % info['shotName']

    print("pre_export_asset - end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    pass


# Hook called after an asset export ends.
#
# info [Dictionary] [Modifiable]
#    Information about the asset exported.
#
#    If the asset is a multi-channel media, the information might only apply to
#    the beauty layer.
#
#    Keys:
#
#    destinationHost: [String]
#       Host name where the exported files were written to.
#
#    destinationPath: [String]
#       Export path root.
#
#    namePattern: [String]
#       List of optional naming tokens.
#
#    resolvedPath: [String]
#       File pattern (relative to destinationPath) that will be exported
#       with all the tokens resolved.
#
#    assetName: [String]
#       Name of the exported asset.
#
#    sequenceName: [String]
#       Name of the sequence the asset is part of.
#
#    shotName: [String]
#       Name of the shot the asset is part of.
#
#    assetType: [String]
#       Type of exported asset.
#       ('video', 'audio', 'movie,' 'batch', 'openClip', 'batchOpenClip', 'distributionPackage')
#
#    isBackground: [Boolean]
#       True if the export of the asset happened in the background.
#
#    backburnerManager: [String]
#       Backburner Manager handling the background job.
#       Empty if job is done in foreground.
#
#    backgroundJobId: [String]
#       Id of the background job given by the backburner Manager upon
#       submission. Empty if job is done in foreground.
#
#    width: [Long]
#       Frame width of the exported asset.
#
#    height: [Long]
#       Frame height of the exported asset.
#
#    aspectRatio: [Double]
#       Frame aspect ratio of the exported asset.
#
#    depth: [String]
#       Frame depth of the exported asset.
#       ('8-bits', '10-bits', '12-bits', '16 fp')
#
#    scanFormat: [String]
#       Scan format of the exported asset.
#       ('FIELD_1', 'FIELD_2', 'PROGRESSIVE')
#
#    colourSpace: [String]
#       Colour space of the exported asset.
#
#    fps: [Double]
#       Frame rate of exported asset.
#
#    sequenceFps: [Double]
#       Frame rate of the sequence the asset is part of.
#
#    sourceIn: [Integer]
#       The source in point as a frame, using the asset frame rate (fps key).
#
#    sourceOut: [Integer]
#       The source out point as a frame, using the asset frame rate (fps key).
#
#    recordIn: [Integer]
#       The record in point as a frame, using the sequence frame rate
#       (sequenceFps key).
#
#    recordOut: [Integer]
#       The record out point as a frame, using the sequence frame rate
#       (sequenceFps key).
#
#    handleIn: [Integer]
#       Head as a frame, using the asset frame rate (fps key).
#
#    handleOut: [Integer]
#       Tail as a frame, using the asset frame rate (fps key).
#
#    track: [String]
#       ID of the sequence's track that contains the asset.
#
#    trackName: [String]
#       Name of the sequence's track that contains the asset.
#
#    segmentIndex: [Integer]
#       Asset index (1 based) in the track.
#
#    versionName: [String]
#       Current version name of export (Empty if unversioned).
#
#    versionNumber: [Integer]
#       Current version number of export (0 if unversioned).
#
# userData [Object] [Modifiable]
#   Object that could have been populated by previous export hooks and that
#   will be carried over into the subsequent export hooks.
#   This can be used by the hook to pass black box data around.
#   This will usually be a dictionary.
#   The object can be modified but not reassigned.
#
def post_export_asset(info, userData, *args, **kwargs):

    print("post_export_asset - start >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    if debug :
        print(info)
        print(userData)
    
    if 'nim_export_sequence' in userData :
        if userData['nim_export_sequence'] == True :
        
            nim_userID = userData['nim_userID']
            
            nim_tapeName = ''
            # Check if tapeName is in info
            # if exists set userData 
            #  - should happen first on batchOpenClip before batch
            if 'tapeName' in info :
                userData['tapeName'] = info['tapeName']
            
            # If tapeName has been sent in userData set var for exportFile
            if 'tapeName' in userData :
                nim_tapeName = userData['tapeName']
            
            # TODO: Correct publishing here
            assetTypeID = 0
            exportFile = False
            if info['assetType'] == 'video' :
                assetTypeID = userData['videoElementID']
            if info['assetType'] == 'audio' :
                assetTypeID = userData['audioElementID']
            if info['assetType'] == 'openClip' :
                assetTypeID = userData['openClipElementID']
            if info['assetType'] == 'batchOpenClip' :
                assetTypeID = userData['batchOpenClipElementID']
            if info['assetType'] == 'batch' :
                assetTypeID = userData['batchTaskTypeID']
                exportFile = True
            
            comment = 'Batch File exported from Flame'
            
            if exportFile :
                # export batch to NIM files
                result = nimFlameExport.nimExportFile(nim_shotID=userData['currentShotID'], info=info, taskTypeID=assetTypeID, \
                                       taskFolder=userData['batchTaskTypeFolder'], serverID=userData['nim_serverID'], \
                                       nim_userID=nim_userID, tapeName=nim_tapeName, comment=comment)
            else :
                # export asset to NIM element
                result = nimFlameExport.nimExportElement(nim_shotID=userData['currentShotID'], info=info, typeID=assetTypeID, nim_userID=nim_userID)
    
    
    if 'nim_export_edit' in userData :
        if userData['nim_export_edit'] == True :
            print("postExportEdit")
            editPath = os.path.join(info['destinationPath'], info['resolvedPath'])
            userData['editData'] = {}
            userData['editData']['path'] = editPath
    
    
    if 'nim_export_daily' in userData :
        if userData['nim_export_daily'] == True :
            print("postExportDaily")
            dailyPath = os.path.join(info['destinationPath'], info['resolvedPath'])
            userData['dailyData'] = {}
            userData['dailyData']['path'] = dailyPath
    
    
    if debug :
        print("destinationPath: %s" % info['destinationPath'])
        print("resolvedPath: %s" % info['resolvedPath'])
        #print "shotName: %s" % info['shotName']
        #print "shotID: %s" % userData['currentShotID']
    
    print("post_export_asset - end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<") 
    
    pass


# :return: true or false whether post_export_asset should be called from a
# backburner job or directly from the application.
#
# :warning: Not generating a post_export_asset backburner job for exports that
# are using backburner could result in post_export_asset being called before the
# export job is complete.
#
def use_backburner_post_export_asset(*args, **kwargs):
    # print "use_backburner_post_export_asset - start"
    return True


# Indicates that the application is about to overwrite a file and the user will
# be prompted with a choice.  This method could be used to bypass the prompt.
#
# Valid return values are:
#    ask : User will be prompted for action.
#    overwrite : Overwrite this file.
#    overwrite_all : Overwrite all file from now on.
#    skip : Do not write the file.
#
def export_overwrite_file(path, *args, **kwargs):
    pass


# Hook returning the custom export profiles to display to the user in the
# contextual menu.
#
# profiles [Dictionary] [Modifiable]
#
#    A dictionary of userData dictionaries where the keys are the name
#    of the profiles to show in contextual menus.
#
def get_custom_export_profiles(profiles, *args, **kwargs):
    print("get_custom_export_profiles - start >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    profiles['rohtau - Publish Sequence']   = {'nim_export_type':'rohtauExportSequence'}   #Adds an entry to the 'userData' dictionary
    profiles['rohtau - Create Review']      = {'nim_export_type':'rohtauExportReview'}       #Adds an entry to the 'userData' dictionary
    # profiles['NIM Publish Sequence']      = {'nim_export_type':'NimExportSequence'}   #Adds an entry to the 'userData' dictionary
    # profiles['NIM Export Review to Show'] = {'nim_export_type':'NimExportEdit'}       #Adds an entry to the 'userData' dictionary
    # profiles['NIM Export Review to Task'] = {'nim_export_type':'NimExportDaily'}      #Adds an entry to the 'userData' dictionary
    
    print("get_custom_export_profiles - end <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    pass


if ( __name__ == "__main__" ):
    import sys

    # Call a hook from the command line:
    #
    #  exportHook.py <function> <args>
    #
    method = sys.argv[1]
    params = (eval(p) for p in sys.argv[2:])
    globals()[method](*params)
