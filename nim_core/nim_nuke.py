#!/usr/bin/env python
#******************************************************************************
#
# Filename: nim_nuke.py
# Version:  v4.0.61.210104
#
# Copyright (c) 2014-2021 NIM Labs LLC
# All rights reserved.
#
# Use of this software is subject to the terms of the NIM Labs license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# *****************************************************************************

# rohtau v0.2

#  General Imports :
# from nim_core.nim_api import get_elementTypes
import os, re, sys
from pprint import pformat

#  NIM Imports :
from . import nim_api as Api
from . import nim_print as P
from . import nim as Nim
from . import nim_rohtau as nimRt
from . import nim_rohtau_utils as nimUtl


from .import version 
from .import winTitle 

#  Nuke Imports :
import nuke

topbuttonsKnobs = ('pubcheckvars', 'pubresetdata')

def get_mainWin() :
    'Returns the name of the main Nuke window'
    
    return

def _knobInfo( nim=None ) :
    'Returns a dictionary of information needed for creating custom NIM knobs in Nuke'
    userInfo=nim.userInfo()
    knobNames=( 'nim_server', 'nim_serverID', 'nim_user', 'nim_userID',
        'nim_job', 'nim_jobID', 'nim_tab', 'nim_asset', 'nim_assetID', 'nim_show', 'nim_showID',
        'nim_shot', 'nim_shotID', 'nim_basename', 'nim_version', 'nim_fileID', 'nim_task', 'nim_taskID', 'nim_type', 'nim_typeID', 'nim_taskFolder', 
        'nim_jobPath', 'nim_shotPath', 'nim_compPath', 'nim_renderPath', 'nim_platesPath', 'nim_pubElements', 'nim_pubTasks', 'nim_APIver' )
    knobLabels=( 'Server Path', 'Server ID', 'User Name', 'User ID',
        'Job Name', 'Job ID', 'Entity', 'Asset Name', 'Asset ID', 'Show Name', 'Show ID',
        'Shot Name', 'Shot ID', 'Basename', 'Version', 'File ID', 'Task Name', 'Task ID', 'Task Type', 'Task Type ID', 'Task Folder', 
        'Job Path', 'Shot Path', 'Comp Path', 'Renders Path', 'Plates Path', 'Publishing Elements', 'Publishing Tasks', 'NIM Version' )
    knobCmds=(  nim.server(), nim.ID('server'), userInfo['name'], userInfo['ID'],
        nim.name('job'), nim.ID('job'), nim.tab(),nim.name('asset'), nim.ID('asset'), nim.name('show'),
        nim.ID('show'), nim.name('shot'), nim.ID('shot'), nim.name('base'), nim.version(), nim.ID('ver'), '', '', nim.name('task'),
        nim.ID('task'), nim.taskFolder(), nim.jobPath(), nim.shotPath(), nim.compPath(), nim.renderPath(), nim.platesPath(),
        str(Api.get_elementTypes()), str(Api.get_taskTypes()), version )
    return ( knobNames, knobLabels, knobCmds )

def set_vars( nim=None ) :
    'Sets the environment variables inside of Nuke, for Deadline to pick up'

    # Debug incoming NIM dictionary
    # from pprint import pformat
    # dictstr = pformat( nim.get_nim(), indent=4)
    # nuke.tprint("NIM Dict:")
    # nuke.tprint(dictstr)

    P.info( 'Setting Nuke Vars...' )
    
    tabName='NIM'
    knobInfo=_knobInfo( nim )
    knobNames, knobLabels, knobCmds=knobInfo[0], knobInfo[1],knobInfo[2]
    #  Get Project Settings Node :
    PS=nuke.root()

    # Rebuild all the UI. Stupid Nuke, seriously, for a tool that cost 8k the scripting is awful. Anyway ....
    for knobname in knobNames:
        if PS.knob(knobname):
            PS.removeKnob(PS.knob(knobname))
    for knobname in topbuttonsKnobs:
        if PS.knob(knobname):
            PS.removeKnob(PS.knob(knobname))
    if PS.knob( tabName ) :
        PS.removeKnob( PS.knob( tabName ) )
    
    #  Create NIM Tab, if it doesn't exist :
    # if not PS.knob( tabName ) :
        # PS.addKnob( nuke.Tab_Knob( tabName ) )
    PS.addKnob( nuke.Tab_Knob( tabName ) )

    # Add top buttons
    topbuttonsLabels = ('Check Pub Data', 'Reset Pub  Data')
    # topbuttonsCmds = ('check_vars()', 'reset_vars()')
    topbuttonsCmds = ('import nim_core.nim_nuke as nimNuke;nimNuke.check_vars()', 'import nim_core.nim_nuke as nimNuke;nimNuke.reset_vars()')
    for button, label, cmd in zip(topbuttonsKnobs, topbuttonsLabels, topbuttonsCmds):
        if not PS.knob( button ):
            PS.addKnob( nuke.PyScript_Knob( button, label, cmd ))
        knob = PS.knob( button )
        knob.setEnabled( True )
    
    #  Create Knobs :
    for x in range(len(knobNames)) :
        if not PS.knob( knobNames[x] ) :
            n = None
            if  knobNames[x].endswith('Path'):
                PS.addKnob( nuke.File_Knob( knobNames[x], knobLabels[x] ))
            elif  knobNames[x].endswith('ID') or knobNames[x].endswith('version'):
                PS.addKnob( nuke.Int_Knob( knobNames[x], knobLabels[x] ))
            elif  knobNames[x] in ('nim_pubElements', 'nim_pubTasks'):
                PS.addKnob( nuke.Multiline_Eval_String_Knob( knobNames[x], knobLabels[x] ))
            else:
                PS.addKnob( nuke.String_Knob( knobNames[x], knobLabels[x] ) )
                # PS.addKnob( nuke.EvalString_Knob( knobNames[x], knobLabels[x] ) )
        #  Set Knob :
        P.debug( '%s - %s' % (knobNames[x], knobCmds[x]) )
        knob=PS.knob( knobNames[x] )
        knob.setEnabled( True )
        if knobCmds[x] :
            #  Convert backslashes to forwardslashes for Nuke :
            if knobNames[x]=='nim_compPath' :
                correctedPath=knobCmds[x].replace( '\\', '/' )
                knob.setValue( correctedPath )
            #  Otherwise, set the knob as normal :
            else :
                if knobNames[x].endswith('ID') or knobNames[x].endswith('version'):
                    # nuke.tprint("Knob Name: %s, String val: %s"%(knobNames[x],knobCmds[x]))
                    knob.setValue( int(knobCmds[x]) )
                elif  knobNames[x] in ('nim_pubElements', 'nim_pubTasks'):
                    knob.setValue( pformat( eval(knobCmds[x]), indent=4 ) )
                else:
                    knob.setValue( knobCmds[x] )
                    
        # knob.setEnabled( False )
        knob.setFlag(nuke.READ_ONLY)

    # Try to find a valid task for the task type and user in the shot/asset
    pubtask  = nimUtl.getuserTask(int(nim.userInfo()['ID']), int(nim.ID('task')), nim.tab().lower(), int(nim.ID('shot')) if nim.tab() == 'SHOT' else int(nim.ID('asset')))
    if not pubtask:
        PS.knob('nim_task').setValue('')
        PS.knob('nim_taskID').setValue(0)
        msg = "Couldn't find a %s task for %s in %s"%(nim.name('task'), nim.userInfo()['name'], nim.name('shot'))
        nimRt.DisplayMessage.get_btn( msg, title= 'Publishing error')
    else:
        PS.knob('nim_task').setValue(pubtask['taskName'])
        PS.knob('nim_taskID').setValue(pubtask['taskID'])


    '''
    tasks = Api.get_taskInfo( itemClass=nim.tab().lower(), itemID=int(nim.ID('shot')) if nim.tab() == 'SHOT' else int(nim.ID('asset')))
    taskfound = False
    for task in tasks:
        if task['typeID'] == str(nim.ID( elem='task' )) and task['userID'] == str(knobCmds[3]):
            PS.knob('nim_task').setValue(str(task['taskName']))
            PS.knob('nim_taskID').setValue(int(task['taskID']))
            taskfound = True
            break
    if not taskfound :
        # hou.ui.setStatusMessage( "Couldn't find a %s task for %s for %s"%(nim.name('task'), userInfo['name'], nim.name('shot')), severity= hou.severityType.Warning)
        taskid = createNIMTaskForRender( PS )
        if taskid:
            PS.knob('nim_task').setValue(nim.name('task'))
            PS.knob('nim_taskID').setValue(taskid)
        else:
            PS.knob('nim_task').setValue('')
            PS.knob('nim_taskID').setValue(0)
            msg = "Couldn't find a %s task for %s for %s"%(nim.name('task'), knobCmds[2], nim.name('shot'))
            nimRt.DisplayMessage.get_btn( msg, title= 'Publishing error')
            # PS.knob('nim_taskFolder').setValue('')
    '''

    
    P.info( 'Done setting Nuke Vars.' )
    
    return

def check_vars():
    'Check current nim dict in nuke file against the publish data returned by NIM'

    '''
    # Check if the script has been saved:
    if nuke.root().name() == 'Root':
        msg = "Script needs to be saved in the publishing system. Use rohtau->Save As"
        nimRt.DisplayMessage.get_btn( msg, title= 'Script Not Saved')
        return False
    '''

    title = 'Check Nuke Script Publish Info'            
    progressTask = nuke.ProgressTask("Check Data")
    progressTask.setMessage("Gather publishing data from file path")
    progressTask.setProgress(0) 
    #  Get API values from file name :
    filepath =  nuke.root()['name'].value() 
    nimdata=Nim.NIM().ingest_filePath( filepath )

    if nimdata is None:
        msg = "Error gathering publish info from: %s \nIs the file saved inside a job structure?"%filepath
        nimRt.DisplayMessage.get_btn( msg, title= 'Publishing error')
        return False
    # # # # from pprint import pformat
    # # # msg = pformat( nimdata.get_nim(), indent=4)
    # # nuke.tprint( "NIM dict from file path: ")
    # nuke.tprint( msg )

    # Get nuke script NIM data
    #  Initialize NIM dictionary :
    progressTask.setMessage("Gather publishing data from Nuke script")
    progressTask.setProgress(50) 
    nim=Nim.NIM()
    nim.ingest_prefs()
    get_vars(nim)
    # print("Nim Nuke Data")
    # from pprint import pformat
    # msg = pformat( nim.get_nim(), indent=4)
    # nuke.tprint( msg )
    #  User :
    # userInfo=nimpubdata.userInfo()

    errors = ""
    iserror = False
    entityIsCorrect = True

    progressTask.setMessage("Compare data")
    progressTask.setProgress(75) 

    # Version:
    if nim.get_nimVer() != version:
        errors += "NIM data saved with a different version of the NIM API. Using NIM %s, data saved using NIM %s"%(version, nim.get_nimVer())
        iserror = True

    # Job
    if nimdata.name('job') != nim.name('job') or nimdata.ID('job') != nim.ID('job') :
        errors += "Job information doesn't match. NIM data (%s,%s) -> Nuke data (%s,%s)\n"%(nimdata.name('job'), nimdata.ID('job'), nim.name('job'), nim.ID('job'))
        iserror = True
    # Job path
    # nimdatajobpath  = os.path.normpath(os.path.join(os.path.normpath(nimdata.name('server')), nimdata.name('job').split()[0]))
    nimdatajobpath = os.path.normpath(os.path.join(os.path.normpath(nimdata.server('path')), nimdata.name('job').split()[0]))
    nimdatajobpath = nimdatajobpath.replace('\\', '/' )
    nimdatajobpath += "/"
    # nimpubjobpath = nimpubdata.name('server') + '/' + nimpubdata.name('job').split()[0]
    if nimdatajobpath != nim.jobPath():
        errors += "Job Path information doesn't match. NIM data: %s -> Nuke data: %s\n"%(nimdatajobpath , nim.jobPath())
        iserror = True
    # Show
    if nimdata.name('show') != nim.name('show') or nimdata.ID('show') != nim.ID('show'):
        errors += "Show/Seq information doesn't match. NIM data (%s,%s) -> Nuke data (%s,%s)\n"%(nimdata.name('show'), nimdata.ID('show'), nim.name('show'), nim.ID('show'))
        iserror = True
    # Shot/Asset
    if (len(nimdata.name('asset')) > 0) !=  (len(nim.name('asset')) > 0):
        errors += "Publish data mismatch for entity type, one is set as asset and the other not\n"
        iserror = True
        entityIsCorrect = False
    if (len(nimdata.name('shot')) > 0) !=  (len(nim.name('shot')) > 0):
        errors += "Publish data mismatch for entity type, one is set as shot and the other not\n"
        iserror = True
        entityIsCorrect = False
    if entityIsCorrect:
        if nim.name('asset'):
            # Asset
            if nimdata.name('asset') != nim.name('asset') or nimdata.ID('asset') != nim.ID('asset'):
                errors += "Asset information doesn't match. NIM data (%s,%s) -> Nuke data (%s,%s)\n"%(nimdata.name('asset'), nimdata.ID('asset'), nim.name('asset'), nim.ID('asset'))
                iserror = True
        elif nim.name('shot'):
            # Shot
            if nimdata.name('shot') != nim.name('shot') or nimdata.ID('shot') != nim.ID('shot'):
                errors += "Shot information doesn't match. NIM data (%s,%s) -> Nuke data (%s,%s)\n"%(nimdata.name('shot'), nimdata.ID('shot'), nim.name('shot'), nim.ID('shot'))
                iserror = True
        else:
            errors += "Nuke Publish data doesn't have information about asset or shot\n"
            iserror = True
    # TODO: shotPath, platesPath, compsPath, rendersPath
    # Task
    progressTask.setMessage("Check available tasks")
    progressTask.setProgress(85) 
    if nimdata.name('task') != nim.name('task') or nimdata.ID('task') != nim.ID('task'):
        errors += "Task information doesn't match. NIM data (%s,%s) -> Nuke data (%s,%s)\n"%(nimdata.name('task'), nimdata.ID('task'), nim.name('task'), nim.ID('task'))
        iserror = True
    # Try to find a valid task for the task type and user in the shot/asset
    tasks = Api.get_taskInfo( itemClass=nimdata.tab().lower(), itemID=int(nimdata.ID('shot')) if nimdata.tab() == 'SHOT' else int(nimdata.ID('asset')))
    taskfound = False
    # nuke.tprint("Search for task:%s, for user %s"%(nimdata.ID('task'), nimdata.ID('user')))
    #  Get Project Settings Node :
    # TODO: refactor this in a function so all apps use the same code to check tasks
    # TODO: use function in API
    PS=nuke.root()
    taskName = PS.knob('nim_task').value()
    taskID = str(int(PS.knob('nim_taskID').value()))
    for task in tasks:
        # nuke.tprint(task)
        # print("Compare task %s with Nim task %s, and user %s with Nim user: %s"%(task['typeID'], nimdata.ID('task'), task['userID'], nimdata.ID('user')))
        if task['typeID'] == nimdata.ID('task') and task['userID'] == str(nimdata.ID('user')):
            # print("Found task %d!"%int(task['taskID']))
            # if int(nim.ID('task')) == 0:
            if int(taskID) == 0:
                errors += "Nuke scene pub data doesn't have task information, but there is a task for this user and this type (%s)\n"%nimdata.name('task')
                iserror = True
            elif (task['taskID'] != taskID) or (task['taskName'] != taskName):
                errors += "Task information doesn't match. NIM data (%s,%s) -> Nuke data (%s,%s)\n"%(task['taskName'], task['taskID'], taskName, taskID)
                iserror = True
            taskfound = True
            break
    if not taskfound and nuke.GUI:
        # hou.ui.setStatusMessage( "Couldn't find a %s task for %s for %s"%(nimpubdata.name('task'), userInfo['name'], nimpubdata.name('shot')), severity= hou.severityType.Warning)
        # nuke.tprint( "Couldn't find a %s task for %s for %s"%(nimdata.name('task'), userInfo['name'], nimdata.name('shot')))
        msg = "Couldn't find a %s task for %s for %s"%(nimdata.name('task'), nimdata.name('user'), nimdata.name('shot'))
        ret = nimRt.DisplayMessage.get_btn( msg, title= title )
    # Version
    if nimdata.version() != nim.version():
        errors += "File version  doesn't match. NIM data %s -> Nuke script data %s\n"%( nimdata.ID('ver'),  nim.ID('ver'))
        iserror = True
    # File ID
    if nimdata.ID('ver') != nim.ID('ver'):
        errors += "File ID doesn't match. NIM data %s -> Nuke script data %s\n"%( nimdata.ID('ver'),  nim.ID('ver'))
        iserror = True
    
    progressTask.setMessage("Completed!")
    progressTask.setProgress(100) 


    if iserror:
        if nuke.GUI:
            # ret = hou.ui.displayMessage( "Some Nuke script publish data failed tests against NIM online publish data:", title='Check Nuke Publish Info',\
                # buttons= ('OK', 'Reset Publish Data'), default_choice=0, close_choice=0, details=errors, details_label='Failed Publish Data',\
                    # severity= hou.severityType.Error)
            nuke.tprint("Publishing data discrepancies:")
            nuke.tprint(errors)
            msg = "Some Nuke scene publish data failed tests against NIM online publish data:"
            buttons = ('OK', 'Reset Publish Data')
            errors += "\n\n"
            ret = nimRt.DisplayMessage.get_btn( msg, title= title, buttons=buttons, default_button=0, details=errors)
            if ret == 1:
                reset_vars( confirm=False )
        else:
            nuke.tprint("Some Nuke scene publish data failed tests against NIM online publish data:")
            nuke.tprint (errors)

    else:
        if nuke.GUI:
            ret = nimRt.DisplayMessage.get_btn( "Nuke script publish data correct", title=title)
        else:
            nuke.tprint("Nuke script publish data correct")

    # Test modal message box:
    # displayMessage("Test")

    return True


def reset_vars( confirm=True ):

    # Check if the script has been saved:
    if nuke.root().name() == 'Root':
        msg = "Script needs to be saved in the publishing system. Use rohtau->Save As"
        nimRt.DisplayMessage.get_btn( msg, title= 'Script Not Saved')
        return False

    if confirm:
        msg = "Do you want to reset scene's publishing data?"
        helpmsg = "Publish information will be worked out using file name and path"
        title = "Reset Scene Publishing Data"
        button = nimRt.DisplayMessage.get_btn( msg, title= title, buttons=('Ok', 'Cancel'), default_button=1)
        if button == 1:
            return
    #  Get API values from file name :
    filepath =  nuke.root()['name'].value() 
    # nuke.tprint("File path: %s"%filepath)
    nimpubdata=Nim.NIM().ingest_filePath( filepath )
    if nimpubdata is None:
        msg = "Error gathering publish info from: %s \nIs the file saved inside a job structure?"%filepath
        nimRt.DisplayMessage.get_btn( msg, title= 'Publishing error')
        return False

    set_vars( nimpubdata )

    if nuke.GUI:
        ret = nimRt.DisplayMessage.get_btn( "Nuke script publish data updated ", title= 'Publishing update')

    return True


def get_vars( nim=None ) :
    'Populates a NIM dictionary with settings from custom NIM Nuke knobs'
    
    knobInfo=_knobInfo( nim )
    knobNames, knobLabels, knobCmds=knobInfo[0], knobInfo[1],knobInfo[2]
    #  Get Project Settings Node :
    PS=nuke.root()
    
    #  Get knob values :
    for x in range(len(knobNames)) :
        if knobNames[x] in PS.knobs().keys() :
            if PS.knob( knobNames[x] ) :
                knob=PS.knob( knobNames[x] )
                #  Tab :
                if knobNames[x]=='nim_tab' :
                    nim.set_tab( _type=knob.value() )
                #  Server :
                elif knobNames[x]=='nim_server' :
                    nim.set_server( path=knob.value() )
                #  Server ID :
                elif knobNames[x]=='nim_serverID' :
                    nim.set_ID( elem='server', ID=str(int(knob.value()))) 
                #  User :
                elif knobNames[x]=='nim_user' :
                    nim.set_user( userName=knob.value() )
                elif knobNames[x]=='nim_userID' :
                    nim.set_userID( userID=str(int(knob.value()))) 
                #  Job :
                elif knobNames[x]=='nim_job' :
                    nim.set_name( elem='job', name=knob.value() )
                elif knobNames[x]=='nim_jobID' :
                    # nuke.tprint( "Job Id Param: %s"%str(int(knob.value())))
                    nim.set_ID( elem='job', ID=str(int(knob.value())) )
                #  Asset :
                elif knobNames[x]=='nim_asset' :
                    nim.set_name( elem='asset', name=knob.value() )
                elif knobNames[x]=='nim_assetID' :
                    nim.set_ID( elem='asset', ID=str(int(knob.value())) if type(knob.value()) is int or type(knob.value()) is float or  len (knob.value()) else '') 
                    nim.set_ID( elem='asset', ID=nim.ID('asset') if nim.ID('asset') != '0' else None) # In the UI an int 0 is actually a None value inside a python dict for NIM
                #  Show :
                elif knobNames[x]=='nim_show' :
                    nim.set_name( elem='show', name=knob.value() )
                elif knobNames[x]=='nim_showID' :
                    nim.set_ID( elem='show', ID=str(int(knob.value())) if type(knob.value()) is int or type(knob.value()) is float or   len (knob.value()) else '') 
                    nim.set_ID( elem='show', ID=nim.ID('show') if nim.ID('show') != '0' else None) # In the UI an int 0 is actually a None value inside a python dict for NIM
                #  Shot :
                elif knobNames[x]=='nim_shot' :
                    nim.set_name( elem='shot', name=knob.value() )
                elif knobNames[x]=='nim_shotID' :
                    nim.set_ID( elem='shot', ID=str(int(knob.value())) if type(knob.value()) is int or type(knob.value()) is float or   len (knob.value()) else '') 
                    nim.set_ID( elem='shot', ID=nim.ID('shot') if nim.ID('shot') != '0' else None) # In the UI an int 0 is actually a None value inside a python dict for NIM
                #  Basename :
                elif knobNames[x]=='nim_basename' :
                    nim.set_name( elem='base', name=knob.value() )
                #  Task :
                elif knobNames[x]=='nim_type' :
                    nim.set_name( elem='task', name=knob.value() )
                elif knobNames[x]=='nim_typeID' :
                    nim.set_ID( elem='task', ID=str(int(knob.value())) if type(knob.value()) is int or type(knob.value()) is float or   len (knob.value()) else '') 
                    nim.set_ID( elem='task', ID=nim.ID('task') if nim.ID('task') != '0' else None) # In the UI an int 0 is actually a None value inside a python dict for NIM
                elif knobNames[x]=='nim_taskFolder' :
                    nim.set_taskFolder( folder=knob.value() )
                # XXX: remember that current task and taskID are not included in the NIM dict
                #  Comp Path :
                elif knobNames[x]=='nim_compPath' :
                    nim.set_compPath( compPath=knob.value() )
                #  Render Path :
                elif knobNames[x]=='nim_renderPath' :
                    nim.set_renderPath( renderPath=knob.value() )
                #  Plates Path :
                elif knobNames[x]=='nim_platesPath' :
                    nim.set_platesPath( platesPath=knob.value() )
                #  Job Path :
                elif knobNames[x]=='nim_jobPath' :
                    nim.set_jobPath( jobPath=knob.value() )
                #  Version :
                elif knobNames[x]=='nim_version' :
                    nim.set_version( str(int(knob.value())) if type(knob.value()) is int or type(knob.value()) is float or   len (knob.value()) else '' )
                    nim.set_version( nim.version() if nim.version() != '0' else None) # In the UI an int 0 is actually a None value inside a python dict for NIM
                #  File ID :
                elif knobNames[x]=='nim_fileID' :
                    nim.set_ID( elem='ver', ID=str(int(knob.value())) if type(knob.value()) is int or type(knob.value()) is float or   len (knob.value()) else '' )
                    nim.set_ID( elem='ver', ID=nim.ID('ver') if nim.ID('ver') != '0' else None) # In the UI an int 0 is actually a None value inside a python dict for NIM
                #  NIM version :
                elif knobNames[x]=='nim_version' :
                    nim.set_nimVer(knob.value())

    return nim

def getTaskNameFromVars(tasktypeid):
    '''
    Look into NIM data in script to get available tasks types and return the name
    that correspond to the given id

    Parameters
    ----------
    tasktypeid : int
        ID for task type

    Returns
    -------
    bool
        False if task info not available in NIM data in script or if task type ID couldnt be found
    '''
    PS = nuke.root()
    tasksKnob = PS.knob('nim_pubTasks')
    if tasksKnob is None:
        error("available tasks information missign in NIM script's data. Please reset Publishing information from rohtau menu")
        return False
    tasks = eval(tasksKnob.value())
    for task in tasks:
        if int(task['ID'].encode('ascii')) == tasktypeid:
            return task['name'].encode('ascii')

    # Not found
    warning("Task with ID %d, not found in Publishing Tasks in NIM script's data"%tasktypeid)
    return False

    pass

def getElementTypeNameFromVars(elmtypeid):
    '''
    Look into NIM data in script to get available element types and return the name
    that correspond to the given id

    Parameters
    ----------
    elmtypeid : int
        ID for element type

    Returns
    -------
    bool
        False if element info not available in NIM data in script or if task type ID couldn't be found
    '''
    PS = nuke.root()
    elmtsKnob = PS.knob('nim_pubElements')
    if elmtsKnob  is None:
        error("Available Element information missing in NIM script's data. Please reset Publishing information from rohtau menu")
        return False
    elmts = eval(elmtsKnob.value())
    for elm in elmts:
        if int(elm['ID'].encode('ascii')) == elmtypeid:
            return elm['name'].encode('ascii')

    # Not found
    warning("Element with ID %d, not found in Publishing Elements in NIM script's data"%elmtypeid)
    return False

    pass

def rndr_mkDir() :
    'Creates the output path for images, if not already existant'
    
    if rndr_dir :
        if not os.path.exists( rndr_dir ) :
            os.makedirs( rndr_dir )
    
    '''
    views=nuke.views()
    file=nuke.filename( nuke.thisNode() )
    dir=os.path.dirname( file )
    osdir=nuke.callbacks.filenameFilter( dir )
    viewdirs=[]
    
    try:
        #  Replacing %V with view name :
        if re.search('%V', dir).group():
            for v in views :
                viewdirs.append(re.sub('%V', v, dir))
    except :
        pass
    
    if len(viewdirs)==0 :
        osdir=nuke.callbacks.filenameFilter(dir)
        if not os.path.isdir( osdir ) :
            os.makedirs( osdir )
    else :
        for vd in viewdirs :
            osdir = nuke.callbacks.filenameFilter( vd )
            if not os.path.isdir(osdir) :
                os.makedirs (osdir)
                print 'Directory (with viewname) created: %s' % (osdir)
    
    #nuke.addBeforeRender(createWriteDir)
    '''
    return

def isGizmo(node):
    return type(node) == 'Gizmo'

def isInsideGroupOrGizmo( node ):
    parent = node.parent()
    return type(parent) == nuke.Gizmo or type(parent) == nuke.Group

def hasNIMData( root ):
    '''
    Detect if the current script has NIM information

    Parameters
    ----------
    root : node
        Nuke's root node

    Returns
    -------
    bool
        True if script has NIM data, otherwise False
    '''
    if root is None:
        return False
    if root is not None and root.knob('nim_compPath') is None:
        nuke.tprint("Script %s doesn't have NIM information"%root.name())
        return False
    return True


def saveRenderScene (renderscene=''):
    '''
    Make snapshot of this nuke script for rendering.    
    The saved scene will be the one to actually be used for rendering

    A path can be provided allowing to create the render scene path outside this function.
    If the path is not provided then the function will generate a path using the timestamp and the 
    pat of the current scene.

    Parameters
    ----------
    renderscene : str
        Path for the render scene, if not provided will be solved internally.

    Raises
    ------
    IOError
        If scene couldn't be saved

    Returns
    -------
    bool
        Path to the renderscene saved, False if any error happens.
    '''
    import stat

    # Save render scene
    scenename = nuke.root().name()
    if not renderscene:
        renderscene =  nimRt.buildRenderSceneName( scenename )
    try:
        nuke.scriptSave( renderscene )
    except :
        P.error("cant save render scene: %s"%renderscene)
        raise 
    # Set file read only
    # mode = os.stat(renderscene).st_mode
    # ro_mask = 0777 ^ (stat.S_IWRITE | stat.S_IWGRP | stat.S_IWOTH)
    # os.chmod(renderscene, mode & ro_mask)    


    return renderscene


def setupWriteForRendering( renderscene, writeNode, fileid=0 ):
    '''
    Do all the mandatory settings needed in a Write node for our pipeline

    Parameter:
    ----------
    renderscene : str
        Path to renderscene
    writeNode : str
        Write node for rendering
    fileid : id
        File ID for published render

    Returns
    -------
    bool
        True if all went well
    '''
    # Create metadata node
    # if isInsideGroupOrGizmo then rather than using writeNode use writeNode.parent() .
    node = writeNode if not isInsideGroupOrGizmo(writeNode) else writeNode.parent() 
    metadatanode = nuke.nodes.ModifyMetaData()
    metadatanode.setName( writeNode.name() + '_metadata' )
    input0 = node.input(0)
    metadatanode.setInput(0, input0)
    node.setInput(0, metadatanode)
    nuke.autoplaceSnap(metadatanode)
    attrsKnob = metadatanode.knob('metadata')
    PS = nuke.root()
    attrs = {}
    try:
        if PS is not None and PS.knob('nim_compPath') is not None:
            # nuke.tprint("Calling to getEXRMetadataAttrsDict with all the publish info")
            attrs = nimRt.getEXRMetadataAttrsDict(  renderscene, os.path.dirname(nuke.filename(node) ), job=PS.knob('nim_job').value().split()[0], jobid=int(PS.knob('nim_jobID').value()),
                                                  show=PS.knob('nim_show').value(), showid=int(PS.knob('nim_showID').value()), shot=PS.knob('nim_shot').value(), 
                                                  shotid=int(PS.knob('nim_showID').value()), asset=PS.knob('nim_asset').value(),
                                                  assetid=int(PS.knob('nim_assetID').value()), fileid=int(fileid))
        else:
            attrs = nimRt.getEXRMetadataAttrsDict(  renderscene, os.path.dirname(nuke.filename(node) ) )
    except ValueError:
        attrs = nimRt.getEXRMetadataAttrsDict(  renderscene, os.path.dirname(nuke.filename(node) ) )
    attrsscript = ""
    for attr in attrs:
        attrsscript += "{set exr/%s %s}\n"%(attr, str(attrs[attr]).replace('\\', '/'))
    attrsKnob.fromScript( attrsscript )
    
    # Write metadata output knob
    outmetadataKnob = writeNode.knob('metadata')
    outmetadataKnob.setValue('all metadata')

    # Sticky Note:
    stickynode = nuke.toNode("__renderStickyNote")
    if stickynode is None:
        stickynode = nuke.createNode('StickyNote', "name %s label \"Render scene from: %s\" note_font_size 20"%("__renderStickyNote", nuke.root().name()) )

    # Disable reading mode for rendering. It cause problems if we are rendering
    # and reading the output from the same script. File descriptor issues:
    if writeNode.knob("tmp_reading") is not None:
        writeNode.knob("tmp_reading").setValue(writeNode.knob('reading').value())

    writeNode.knob('reading').setValue(False)

    return True

def restoreRenderingSetup( writeNode ):
    '''
    Restore changes made by se

    Arguments:
        writeNode {nuke.Node} -- Write node for rendering

    Returns:
        bool -- True if all went well
    '''
    metadatanode = nuke.toNode(writeNode.name() + '_metadata')
    if metadatanode is None:
        P.error("Missing Metadata node for %s. Render scene setup is incorrect"%writeNode.name())
        return False
    nuke.delete(metadatanode)
    stickynode = nuke.toNode("__renderStickyNote")
    if stickynode  is not None:
        nuke.delete(stickynode)

    # Restore reading state
    if writeNode.knob("tmp_reading") is not None:
        writeNode.knob("reading").setValue(writeNode.knob('tmp_reading').value())
    
    return True

def getNIMTaskForRender( root ):
    '''
    Looking at the NIM data, check if there is a task of the type specified in the NIM data for the
    user who published the file in the Asset/Shot this script has been saved to

    Parameters
    ----------
    root : node
        Nuke's root node

    Returns
    -------
    int
        Task ID if a task exists otherwise False
    '''
    tab        = root.knob('nim_tab').value()
    task       = root.knob('nim_type').value()
    taskTypeID = root.knob('nim_typeID').value()
    user       = root.knob('nim_user').value()
    userID     = root.knob('nim_userID').value()
    entity     = root.knob('nim_shot').value() if root.knob('nim_tab').value() == 'SHOT' else root.knob('nim_asset').value()
    entityID   = root.knob('nim_shotID').value() if root.knob('nim_tab').value() == 'SHOT' else root.knob('nim_assetID').value()
    tasks      = Api.get_taskInfo( itemClass=tab.lower(), itemID=entityID )
    taskfound  = False
    for task in tasks:
        if int(task['typeID']) == taskTypeID and int(task['userID']) == userID:
            return int(task['taskID'])
            taskfound = True
    return False


def createNIMTaskForRender( root ):
    '''
    Looking at the NIM data, create a task of the type specified in the NIM data for the
    user who published the file in the Asset/Shot this script has been saved to

    Parameters
    ----------
    root : node
        Nuke's root node

    Returns
    -------
    bool
        True if a task already exists or has been created correctly, otherwise False
    '''
    if not hasNIMData(root):
        return False
    taskID = getNIMTaskForRender( root )
    if not taskID:
        tab      = root.knob('nim_tab').value()
        task     = root.knob('nim_type').value()
        user     = root.knob('nim_user').value()
        userID   = root.knob('nim_userID').value()
        entity   = root.knob('nim_shot').value() if root.knob('nim_tab').value() == 'SHOT' else root.knob('nim_asset').value()
        entityID = root.knob('nim_shotID').value() if root.knob('nim_tab').value() == 'SHOT' else root.knob('nim_assetID').value()
        res      = nuke.ask("Couldn't find a task of type %s in %s %s for %s.\nTo publish renders correctly a task must be created. Do you want to create a %s task for you?"%(task, root.knob('nim_tab').value().lower(), entity, user, task))
        if res:
            # Create task
            taskTypeId = nimUtl.gettaskTypesIdFromName( task )
            msg = "%s task created by %s when opening scene"%(task, user)
            taskres = Api.add_task( assetID=entityID if tab == 'ASSET' else None, shotID=entityID if tab == 'SHOT' else None,
                                   taskTypeID=taskTypeId, userID=int(userID), taskStatusID=2, description=msg) 
            if taskres['success'] != 'true':
                nuke.error("Error creating task of type %s in %s %s for %s.\nPlease contact production to get the task created for you or our #support channel"%(task, root.knob('nim_tab').value().lower(), entity, user))
                return False
            else:
                nuke.message("Task successfully created!")
                P.info("Task %s created for %s: %d"%(task, user, int(taskres['ID']) ))
                # return int(taskres['taskID'])
                nuke.tprint(pformat(taskres))
                return int(taskres['ID'])
        else:
            # Abort
            return False
    else:
        return taskID

    pass

#  Create Custom NIM Node :
#===-----------------------------------

class NIM_Node() :
    
    def __init__( self, nodeType='read' ) :
        'Creates a custom NIM Read/Write node'
        
        if nodeType.lower() in ['write'] :
            nodeType='Write'
            nodeName='NIM_WriteNode'
        elif nodeType.lower() in ['read'] :
            nodeType='Read'
            nodeName='NIM_ReadNode'
        
        P.info( '\nCreating %s node\n' % nodeType )
        
        #  Create node :
        node=nuke.createNode( nodeType )
        
        count=1
        #  Get unique node name :
        while nuke.exists( '%s_%03d' % ( nodeName, count ) ) :
            count +=1
        node.knob( 'name' ).setValue( '%s_%03d' % ( nodeName, count ) )
        
        #  Create a Tab :
        tab=nuke.Tab_Knob( 'NIM' )
        node.addKnob( tab )
        
        self.nim={}
        #  Initialize the main dictionary :
        self.elements=['job', 'show', 'shot', 'task', 'base', 'ver']
        for elem in self.elements :
            elemDict={}
            elemDict['name']=''
            elemDict['ID']=None
            elemDict['IDs']=[]
            elemDict['list']=[]
            elemDict['input']=None
            self.nim[elem]=elemDict
        
        #  Add custom knobs :
        self.nim['job']['input']=nuke.Enumeration_Knob( 'job_input', 'Job:', \
            ['xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'] )
        self.nim['show']['input']=nuke.Enumeration_Knob( 'show_input', 'Show:', \
            ['xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'] )
        self.nim['shot']['input']=nuke.Enumeration_Knob( 'shot_input', 'Shot:', \
            ['xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'] )
        self.nim['task']['input']=nuke.Enumeration_Knob( 'task_input', 'Task:', \
            ['xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'] )
        self.nim['base']['input']=nuke.Enumeration_Knob( 'base_input', 'Basename:', \
            ['xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'] )
        self.nim['ver']['input']=nuke.Enumeration_Knob( 'ver_input', 'Version', \
            ['xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'] )
        
        #  Add knobs to tab :
        for knob in [self.nim['job']['input'], self.nim['show']['input'], self.nim['shot']['input'], self.nim['task']['input'], \
            self.nim['base']['input'], self.nim['ver']['input']] :
            node.addKnob( knob )
        
        self.elem_populate( 'job' )
        self.elem_populate( 'show' )
        self.elem_populate( 'shot' )
        self.elem_populate( 'task' )
        self.elem_populate( 'base' )
        self.elem_populate( 'ver' )
        
        #  Hook up knobs :
        nuke.addKnobChanged( self.knob_changed )
        
        return
    
    
    def elem_populate( self, elem='' ) :
        'Populates each of the combo boxes, when specified'
        
        if elem is not 'job' :
            prevElem=self.elements[self.elements.index(elem)-1]
        
        if elem=='job' :
            #  Get jobs :
            jobs=Api.get_jobs()
            if jobs and len(jobs) :
                P.log( 'Jobs Dictionary = %s' % jobs ) 
                #  List of IDs will always be one behind index of 'list', due to "Select..." :
                self.nim[elem]['list'].append( 'Select...' )
                for job in jobs :
                    self.nim[elem]['list'].append( job )
                    self.nim[elem]['IDs'].append( jobs[job] )
                #  Populate combo box :
                self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
            else :
                self.nim[elem]['IDs']=[]
                self.nim[elem]['list']=['None']
                self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
        
        if elem=='show' :
            self.nim[prevElem]['name']=self.nim[prevElem]['list'][int(self.nim[prevElem]['input'].getValue())]
            if self.nim[prevElem]['name'] not in ['Select...', 'None', ''] :
                self.nim[prevElem]['ID']=self.nim[prevElem]['IDs'][int(self.nim[prevElem]['input'].getValue())-1]
                P.log( 'Job = %s, JobID = %s' % ( self.nim[prevElem]['name'], self.nim[prevElem]['ID'] ) )
                shows=Api.get_shows( self.nim[prevElem]['name'] )
                if shows and len(shows) :
                    P.log( 'Shows Dictionary = %s' % shows ) 
                    self.nim[elem]['list']=[]
                    self.nim[elem]['IDs']=[]
                    #  List of IDs will always be one behind index of 'list', due to "Select..." :
                    self.nim[elem]['list'].append( 'Select...' )
                    for show in shows :
                        self.nim[elem]['list'].append( show )
                        self.nim[elem]['IDs'].append( shows[show] )
                    #  Populate combo box :
                    self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                    self.nim[elem]['input'].setValue(0)
                else :
                    self.nim[elem]['IDs']=[]
                    self.nim[elem]['list']=['None']
                    self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                    self.nim[elem]['input'].setValue(0)
            else :
                self.nim[prevElem]['ID']=None
                self.nim[elem]['IDs']=[]
                self.nim[elem]['list']=['None']
                self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                self.nim[elem]['input'].setValue(0)
        
        if elem=='shot' :
            self.nim[prevElem]['name']=self.nim[prevElem]['list'][int(self.nim[prevElem]['input'].getValue())]
            if self.nim[prevElem]['name'] not in ['Select...', 'None', ''] :
                self.nim[prevElem]['ID']=self.nim[prevElem]['IDs'][int(self.nim[prevElem]['input'].getValue())-1]
                P.log( 'Show = %s, ShowID = %s' % ( self.nim[prevElem]['name'], self.nim[prevElem]['ID'] ) )
                shots=Api.get_shots( self.nim[prevElem]['ID'] )
                if shots and len(shots) :
                    P.log( 'Shot Dictionary = %s' % shots ) 
                    self.nim[elem]['list']=[]
                    self.nim[elem]['IDs']=[]
                    #  List of IDs will always be one behind index of 'list', due to "Select..." :
                    self.nim[elem]['list'].append( 'Select...' )
                    for shot in shots :
                        self.nim[elem]['list'].append( shot['name'] )
                        self.nim[elem]['IDs'].append( shot['ID'] )
                    #  Populate combo box :
                    self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                    self.nim[elem]['input'].setValue(0)
                else :
                    self.nim[elem]['IDs']=[]
                    self.nim[elem]['list']=['None']
                    self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                    self.nim[elem]['input'].setValue(0)
            else :
                self.nim[prevElem]['ID']=None
                self.nim[elem]['IDs']=[]
                self.nim[elem]['list']=['None']
                self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                self.nim[elem]['input'].setValue(0)
        
        if elem=='task' :
            self.nim[prevElem]['name']=self.nim[prevElem]['list'][int(self.nim[prevElem]['input'].getValue())]
            if self.nim[prevElem]['name'] not in ['Select...', 'None', ''] :
                self.nim[prevElem]['ID']=self.nim[prevElem]['IDs'][int(self.nim[prevElem]['input'].getValue())-1]
                P.log( 'Shot = %s, ShotID = %s' % ( self.nim[prevElem]['name'], self.nim[prevElem]['ID'] ) )
                self.nim[elem]['list']=['Comp']
                self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                self.nim[elem]['input'].setValue(1)
            else :
                self.nim['show']['ID']=None
                self.nim[elem]['IDs']=[]
                self.nim[elem]['list']=['None']
                self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                self.nim[elem]['input'].setValue(1)
        
        if elem=='base' :
            self.nim[prevElem]['name']=self.nim[prevElem]['list'][int(self.nim[prevElem]['input'].getValue())]
            if self.nim[prevElem]['name'] not in ['Select...', 'None', ''] :
                bases=Api.get_bases( shotID=self.nim['shot']['ID'], task='COMP' )
                if bases and len(bases) :
                    self.nim[elem]['list']=[]
                    if len(bases)>1 :
                        P.log( 'Basenames Dictionary = %s' % bases ) 
                        #  List of IDs will always be one behind index of 'list', due to "Select..." :
                        self.nim[elem]['list'].append( 'Select...' )
                        for base in bases :
                            self.nim[elem]['list'].append( base['basename'] )
                        #  Populate combo box :
                        self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                        self.nim[elem]['input'].setValue(0)
                    else :
                        self.nim[elem]['list']=[bases[0]['basename']]
                        self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                        self.nim[elem]['input'].setValue(0)
                else :
                    self.nim[elem]['IDs']=[]
                    self.nim[elem]['list']=['None']
                    self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                    self.nim[elem]['input'].setValue(0)
            else :
                self.nim[prevElem]['ID']=None
                self.nim[elem]['IDs']=[]
                self.nim[elem]['list']=['None']
                self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                self.nim[elem]['input'].setValue(0)
        
        if elem=='ver' :
            self.nim[prevElem]['name']=self.nim[prevElem]['list'][int(self.nim[prevElem]['input'].getValue())]
            if self.nim[prevElem]['name'] not in ['Select...', 'None', ''] :
                vers=Api.get_vers( shotID=self.nim['shot']['ID'], basename=self.nim['base']['name'] )
                if vers and len(vers) :
                    self.nim[elem]['list']=[]
                    #  List of IDs will always be one behind index of 'list', due to "Select..." :
                    self.nim[elem]['list'].append( 'Select...' )
                    for ver in vers :
                        print ver
                        if nuke.env['nc'] :
                            srch=re.search( '_[v]?[0-9]+.nknc$', ver['filename'] )
                        else :
                            srch=re.search( '_[v]?[0-9]+.nk$', ver['filename'] )
                        if srch :
                            verNum=re.search( '[0-9]+', srch.group() )
                            if verNum :
                                self.nim[elem]['list'].append( str(int(verNum.group())) )
                                self.nim[elem]['IDs'].append( ver['fileID'] )
                    #  Populate combo box :
                    self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                    self.nim[elem]['input'].setValue(0)
                else :
                    self.nim[elem]['IDs']=[]
                    self.nim[elem]['list']=['None']
                    self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                    self.nim[elem]['input'].setValue(0)
            else :
                self.nim[prevElem]['ID']=None
                self.nim[elem]['IDs']=[]
                self.nim[elem]['list']=['None']
                self.nim[elem]['input'].setValues( self.nim[elem]['list'] )
                self.nim[elem]['input'].setValue(0)
        
        return
    
    
    def knob_changed( self ) :
        'Run every time a knob is manipulated.'
        
        if nuke.thisKnob()==self.nim['job']['input'] :
            self.elem_populate( 'show' )
            self.elem_populate( 'shot' )
            self.elem_populate( 'task' )
            self.elem_populate( 'base' )
            self.elem_populate( 'ver' )
        if nuke.thisKnob()==self.nim['show']['input'] :
            self.elem_populate( 'shot' )
            self.elem_populate( 'task' )
            self.elem_populate( 'base' )
            self.elem_populate( 'ver' )
        if nuke.thisKnob()==self.nim['shot']['input'] :
            self.elem_populate( 'task' )
            self.elem_populate( 'base' )
            self.elem_populate( 'ver' )
        if nuke.thisKnob()==self.nim['task']['input'] :
            self.elem_populate( 'base' )
            self.elem_populate( 'ver' )
        if nuke.thisKnob()==self.nim['base']['input'] :
            self.elem_populate( 'ver' )
        if nuke.thisKnob()==self.nim['ver']['input'] :
            pass
            #self.elem_populate( '' )
        
        nuke.callbacks.updateUI()
        
        return

#  End of Class

# End
