#!/usr/bin/env python
#******************************************************************************
#
# Filename: nim_houdini.py
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
import os, sys, traceback
import nim as Nim
import nim_file as F
import nim_print as P
import nim_api as Api
import nim_rohtau as Rt
import nim_rohtau_utils as Utl
from pprint import pprint
#  Houdini Imports :
import hou
#  Import Python GUI packages :
try : from PySide import QtCore, QtGui
except :
    try : from PyQt4 import QtCore, QtGui
    except : pass

#  Variables :
# version='v4.0.61'
# winTitle='NIM_'+version
from .import version 
from .import winTitle 


def get_mainWin() :
    'Returns the name of the main Houdini window'
    import hou
    #maxWin=MaxPlus.Win32_GetMAXHWnd()
    #return maxWin
    return True

# def set_vars( nim=None ) :
def set_vars( nim ) :
    'Add variables to Houdini Globals'
    
    P.info( '\nHoudini - Setting Globals variables...' )

    if nim is None:
        raise hou.OperationFailed( "ERROR: empty NIM dictionary. Can't save publising information into hip file")

    # help(nim)
    # print("================================")
    # from pprint import pprint
    # pprint(nim.get_nim())

    #  User :
    userInfo=nim.userInfo()

    makeGlobalAttrs = False
    h_root = hou.node("/")
    
    h_root.setUserData("nim_version", str(version)) 

    h_root.setUserData("nim_user", str(userInfo['name'])) 
    h_root.setUserData("nim_userID", str(userInfo['ID'])) 
    h_root.setUserData("nim_class", str(nim.tab())) 
    h_root.setUserData("nim_server", str(nim.server())) 
    h_root.setUserData("nim_serverID", str(nim.ID('server'))) 
    h_root.setUserData("nim_jobName", str(nim.name('job'))) 
    h_root.setUserData("nim_jobID", str(nim.ID('job'))) 
    h_root.setUserData("nim_showName", str(nim.name('show'))) 
    h_root.setUserData("nim_showID", str(nim.ID('show'))) 
    h_root.setUserData("nim_shot", str(nim.name('shot'))) 
    h_root.setUserData("nim_shotID", str(nim.ID('shot'))) 
    h_root.setUserData("nim_asset", str(nim.name('asset'))) 
    h_root.setUserData("nim_assetID", str(nim.ID('asset'))) 
    h_root.setUserData("nim_fileID", str(nim.ID('ver')))

    if nim.tab()=='SHOT' :
        h_root.setUserData("nim_name", str(nim.name('shot')))
    elif nim.tab()=='ASSET' :
        h_root.setUserData("nim_name", str(nim.name('asset')))

    h_root.setUserData("nim_basename", str(nim.name('base'))) 
    h_root.setUserData("nim_type", str(nim.name( elem='task'))) 
    h_root.setUserData("nim_typeID", str(nim.ID( elem='task' ))) 
    h_root.setUserData("nim_typeFolder", str(nim.taskFolder())) 
    h_root.setUserData("nim_tag", str(nim.name('tag'))) 
    h_root.setUserData("nim_fileType", str(nim.fileType())) 
    h_root.setUserData("nim_jobPath", str(nim.jobPath())) 
    h_root.setUserData("nim_shotPath", str(nim.shotPath())) 
    h_root.setUserData("nim_renderPath", str(nim.renderPath())) 
    h_root.setUserData("nim_compPath", str(nim.compPath())) 
    h_root.setUserData("nim_platesPath", str(nim.platesPath())) 
    h_root.setUserData("nim_pubElements", str(nim.get_elementTypes())) 
    # Try to check a valid task for the task type and user in the shot/asset
    pubtask  = Utl.getuserTask(int(nim.userInfo()['ID']), int(nim.ID('task')), nim.tab().lower(), int(nim.ID('shot')) if nim.tab() == 'SHOT' else int(nim.ID('asset')))
    if not pubtask:
        h_root.setUserData("nim_task", '')
        h_root.setUserData("nim_taskID", '0') 
        hou.ui.setStatusMessage( "Couldn't find a %s task for %s for %s"%(nim.name('task'), userInfo['name'], nim.name('shot')), severity= hou.severityType.Warning)
    else:
        h_root.setUserData("nim_task", str(pubtask['taskName']))
        h_root.setUserData("nim_taskID", str(pubtask['taskID'])) 
    '''
    # Try to find a valid task for the task type and user in the shot/asset
    pubtask  = Utl.getuserTask(int(nim.userInfo()['ID']), int(nim.ID('task')), nim.tab().lower(), int(nim.ID('shot')) if nim.tab() == 'SHOT' else int(nim.ID('asset')))
    if not pubtask:
        h_root.setUserData("nim_task", '')
        h_root.setUserData("nim_taskID", '0') 
        hou.ui.setStatusMessage( "Couldn't find a %s task for %s for %s"%(nim.name('task'), userInfo['name'], nim.name('shot')), severity= hou.severityType.Error)
        hou.ui.displayMessage( "Couldn't find a %s task for %s for %s"%(nim.name('task'), userInfo['name'], nim.name('shot')), title='Scene publish error', 
                              help='Please create a task for this scene from the rohtau menu', 
                              details='If there is no valid task for this scene, any publishing, like reneders or caches will fail', 
                              severity= hou.severityType.Error)
    else:
        h_root.setUserData("nim_task", str(pubtask['taskName']))
        h_root.setUserData("nim_taskID", str(pubtask['taskID'])) 
    '''
    '''
    pubtask = Utl.getuserTask(int(userInfo['ID']), int(nim.ID(elem='task')), nim.tab().lower(), int(nim.ID('shot')) if nim.tab() == 'SHOT' else int(nim.ID('asset')))
    if pubtask:
        h_root.setUserData("nim_task", str(pubtask['taskName']))
        h_root.setUserData("nim_taskID", str(pubtask['taskID'])) 
    # tasks = Api.get_taskInfo( itemClass=nim.tab().lower(), itemID=int(nim.ID('shot')) if nim.tab() == 'SHOT' else int(nim.ID('asset')))
    # taskfound = False
    # for task in tasks:
        # if task['typeID'] == str(nim.ID( elem='task' )) and task['userID'] == str(userInfo['ID']):
            # print("Found task %d!"%int(task['taskID']))
            # print(task)
            # h_root.setUserData("nim_task", str(task['taskName']))
            # h_root.setUserData("nim_taskID", str(task['taskID'])) 
            # taskfound = True
            # break
    if not pubtask and hou.isUIAvailable():
        hou.ui.setStatusMessage( "Couldn't find a %s task for %s for %s"%(nim.name('task'), userInfo['name'], nim.name('shot')), severity= hou.severityType.Warning)
        h_root.setUserData("nim_task", '')
        h_root.setUserData("nim_taskID", '0') 
    '''

    
    P.info("Publishing information added to HIP")

    # Set env vars used by nodes:
    hou.putenv( 'SHOW', h_root.userData('nim_jobName'))
    hou.putenv( 'SHOT', h_root.userData('nim_name'))
    hou.putenv( 'SHOWPATH', h_root.userData('nim_jobPath'))
    hou.putenv( 'SHOTPATH', h_root.userData('nim_shotPath'))
    hou.putenv( 'SHOTRENDERSPATH', h_root.userData('nim_renderPath'))
    hou.putenv( 'SHOTCOMPSPATH', h_root.userData('nim_compPath'))
    hou.putenv( 'SHOTPLATESPATH', h_root.userData('nim_platesPath'))
    hou.putenv( 'TASK', h_root.userData('nim_task'))

    P.info("Session env vars updated with Publishing data")

    return

def dump_vars( ):
    from pprint import pformat

    dump = "HIP file Publishing data from NIM:\n"
    dump += pformat( hou.node('/').userDataDict(), indent=2, depth=4 )
    dump += "\n\n Session environment variables:\n"
    sessionvars = ('SHOW', 'SHOT', 'SHOWPATH', 'SHOTPATH', 'SHOTRENDERSPATH', 'SHOTCOMPSPATH', 'SHOTPLATESPATH', 'TASK')
    # sessionvarssrc = ('nim_jobName', 'nim_name', 'nim_jobPath', 'nim_shotPath', 'nim_renderPath', 'nim_compPath', 'nim_platesPath', 'nim_task')
    for var in sessionvars:
        dump += "%s %s %s\n"%(var, "=>".rjust(25), hou.getenv(var))
    
    title = "NIM Publish info for: %s"%hou.expandString('HIPFILE')
    if hou.isUIAvailable():
        ret = hou.ui.displayMessage( dump, title=title, buttons=('OK','Check Publish Info'), close_choice=0 )
        if ret == 1:
            # Call check data
            check_vars()
    else:
        print( title )
        print( dump )
        print( '####################' )
            
    
    return True
    
def check_vars():
    'Check current nim dict in hip file agains the publish data returned by NIM'

    #  Get API values from file name :
    nimpubdata=Nim.NIM().ingest_filePath( hou.hipFile.name() )
    if nimpubdata is None:
        hou.ui.displayMessage('Error gathering publish info from File Name', title='Publishing error', severity=hou.severityType.Error)
    # print("Nim Pub Data")
    # from pprint import pprint
    # pprint( nimpubdata.get_nim(), indent=4)

    # Get hip NIM data
    nimhipdata = hou.node('/').userDataDict()
    #  User :
    userInfo=nimpubdata.userInfo()

    errors = ""
    iserror = False
    entityIsCorrect = True

    # Version:
    if 'nim_version' not in nimhipdata or nimhipdata['nim_version'] != version:
        errors += "NIM data saved with a different version of the NIM API. Using NIM %s, data saved using NIM %s"%(version, nimhipdata['nim_version'] if 'nim_version' in nimhipdata else 'N/A')
        iserror = True

    # Job
    if nimpubdata.name('job') != nimhipdata['nim_jobName'] or nimpubdata.ID('job') != nimhipdata['nim_jobID']:
        errors += "Job information doesn't match. NIM data (%s,%s) -> HIP data (%s,%s)\n"%(nimpubdata.name('job'), nimpubdata.ID('job'), nimhipdata['nim_jobName'], nimhipdata['nim_jobID'])
        iserror = True
    # Job path
    nimpubjobpath = os.path.normpath(os.path.join(os.path.normpath(nimpubdata.server('path')), nimpubdata.name('job').split()[0]))
    nimpubjobpath = Rt.toPosix( nimpubjobpath, force=True )
    # nimpubjobpath = nimpubdata.name('server') + '/' + nimpubdata.name('job').split()[0]
    if nimpubjobpath != nimhipdata['nim_jobPath']:
        errors += "Job Path information doesn't match. NIM data %s -> HIP data %s\n"%(nimpubjobpath, nimhipdata['nim_jobPath'])
        iserror = True
    # Show
    if nimpubdata.name('show') != nimhipdata['nim_showName'] or nimpubdata.ID('show') != nimhipdata['nim_showID']:
        errors += "Show/Seq information doesn't match. NIM data (%s,%s) -> HIP data (%s,%s)\n"%(nimpubdata.name('show'), nimpubdata.ID('show'), nimhipdata['nim_showName'], nimhipdata['nim_showID'])
        iserror = True
    # Shot/Asset
    if (len(nimpubdata.name('asset')) > 0) !=  (len(nimhipdata['nim_asset']) > 0):
        errors += "Publish data mismatch for entity type, one is set as asset and the other not\n"
        iserror = True
        entityIsCorrect = False
    if (len(nimpubdata.name('shot')) > 0) !=  (len(nimhipdata['nim_shot']) > 0):
        errors += "Publish data mismatch for entity type, one is set as shot and the other not\n"
        iserror = True
        entityIsCorrect = False
    if entityIsCorrect:
        if nimhipdata['nim_asset']:
            # Asset
            if nimpubdata.name('asset') != nimhipdata['nim_asset'] or nimpubdata.ID('asset') != nimhipdata['nim_assetID']:
                errors += "Asset information doesn't match. NIM data (%s,%s) -> HIP data (%s,%s)\n"%(nimpubdata.name('asset'), nimpubdata.ID('asset'), nimhipdata['nim_asset'], nimhipdata['nim_assetID'])
                iserror = True
        elif nimhipdata['nim_shot']:
            # Shot
            if nimpubdata.name('shot') != nimhipdata['nim_shot'] or nimpubdata.ID('shot') != nimhipdata['nim_shotID']:
                errors += "Shot information doesn't match. NIM data (%s,%s) -> HIP data (%s,%s)\n"%(nimpubdata.name('shot'), nimpubdata.ID('shot'), nimhipdata['nim_shot'], nimhipdata['nim_shotID'])
                iserror = True
        else:
            errors += "HIP Publish data doesn't have information about asset or shot\n"
            iserror = True
    # TODO: shotPath, platesPath, compsPath, rendersPath
    # Task
    if nimpubdata.name('task') != nimhipdata['nim_type'] or nimpubdata.ID('task') != nimhipdata['nim_typeID']:
        errors += "Task information doesn't match. NIM data (%s,%s) -> HIP data (%s,%s)\n"%(nimpubdata.name('task'), nimpubdata.ID('task'), nimhipdata['nim_type'], nimhipdata['nim_typeID'])
        iserror = True
    # Try to find a valid task for the task type and user in the shot/asset
    pubtask = Utl.getuserTask(int(nimpubdata.ID('user')), int(nimpubdata.ID('task')), nimpubdata.get_nim()['class'].lower(), int(nimpubdata.ID('shot')) if nimpubdata.get_nim()['class'] == 'SHOT' else int(nimpubdata.ID('asset')))
    # pprint(pubtask)
    if pubtask:
        if 'nim_taskID' not in nimhipdata:
            errors += "HIP data doesn't have task information, but there is a task for this user and this type (%s)\n"%nimpubdata.name('task')
            iserror = True
        elif (pubtask['taskID'] != nimhipdata['nim_taskID']) or (pubtask['taskName'] != nimhipdata['nim_task']):
            errors += "Task information doesn't match. NIM data (%s,%s) -> HIP data (%s,%s)\n"%(task['taskName'], task['taskID'], nimhipdata['nim_task'], nimhipdata['nim_taskID'])
            iserror = True
        
    if not pubtask and hou.isUIAvailable():
        hou.ui.setStatusMessage( "Couldn't find a %s task for %s for %s"%(nimpubdata.name('task'), userInfo['name'], nimpubdata.name('shot')), severity= hou.severityType.Warning)
    # Version
    if nimpubdata.ID('ver') != nimhipdata['nim_fileID']:
        errors += "File version ID information doesn't match. NIM data %s -> HIP data %s\n"%( nimpubdata.ID('ver'),  nimhipdata['nim_fileID'])
        iserror = True
    


    if iserror:
        if hou.isUIAvailable():
            ret = hou.ui.displayMessage( "Some HIP file publish data failed tests against NIM online publish data:", title='Check HIP Publish Info',\
                buttons= ('OK', 'Reset Publish Data'), default_choice=0, close_choice=0, details=errors, details_label='Failed Publish Data',\
                    severity= hou.severityType.Error)
            if ret == 1:
                reset_vars( confirm=False )
        else:
            print("Some HIP file publish data failed tests against NIM online publish data:")
            print (errors)

    else:
        if hou.isUIAvailable():
            hou.ui.displayMessage( "HIP publish data correct", title='Check HIP Publishing data' )
        else:
            print("HIP publish data correct")

    return True

def reset_vars( confirm=True ):

    if confirm:
        msg = "Do you want to reset scene's publishing data?"
        helpmsg = "Publish information will be worked out using file name and path"
        title = "Reset Scene Publishing Data"
        if not hou.ui.displayConfirmation( msg, severity=hou.severityType.Warning, help=helpmsg, title=title):
            return
    #  Get API values from file name :
    nimpubdata=Nim.NIM().ingest_filePath( hou.hipFile.name() )
    if nimpubdata is None:
        hou.ui.displayMessage('Error gathering publish info from File Name', title='Publishing error', severity=hou.severityType.Error)
        return False

    set_vars( nimpubdata )

    if hou.isUIAvailable():
        hou.ui.setStatusMessage( "HIP file publish data updated ", severity= hou.severityType.ImportantMessage)

    return True

def get_vars( nim=None ) :
    'Gets NIM settings from the root node in Houdini.'
    P.info('Getting information from NIM attributes on the root node...')
    
    h_root = hou.node("/")

    #  User :
    nim_user = h_root.userData("nim_user")
    if nim_user is not None:
        nim.set_user( userName=nim_user )
        P.info('Reading userName')
    else:
        P.error('Failed reading userName')



    #  User ID :
    nim_userID = h_root.userData("nim_userID")
    if nim_userID is not None:
        nim.set_userID( userID=nim_userID )
        P.info('Reading userID')
    else:
        P.error('Failed reading userID')

    #  Tab/Class :
    nim_class = h_root.userData("nim_class")
    if nim_class is not None:
        nim.set_tab( nim_class )
        P.info('Reading nim_class')
    else:
        P.error('Failed reading nim_class')




    #  Server :
    nim_server = h_root.userData("nim_server")
    if nim_server is not None:
        nim.set_server( path=nim_server )
        P.info('Reading nim_server')
    else:
        P.error('Failed reading nim_server')


    #  Server ID :
    nim_serverID = h_root.userData("nim_serverID")
    if nim_serverID is not None:
        nim.set_ID( elem='server', ID=nim_serverID )
        P.info('Reading nim_serverID')
    else:
        P.error('Failed reading nim_serverID')



    #  Job :
    nim_jobName = h_root.userData("nim_jobName")
    if nim_jobName is not None:
        nim.set_name( elem='job', name=nim_jobName )
        P.info('Reading nim_jobName')
    else:
        P.error('Failed reading nim_jobName')


    #  Job ID :
    nim_jobID = h_root.userData("nim_jobID")
    if nim_jobID is not None:
        nim.set_ID( elem='job', ID=nim_jobID )
        P.info('Reading nim_jobID')
    else:
        P.error('Failed reading nim_jobID')



    #  Show :
    nim_showName = h_root.userData("nim_showName")
    if nim_showName is not None:
        nim.set_name( elem='show', name=nim_showName )
        P.info('Reading nim_showName')
    else:
        P.error('Failed reading nim_showName')



    #  Show ID :
    nim_showID = h_root.userData("nim_showID")
    if nim_showID is not None:
        nim.set_ID( elem='show', ID=nim_showID )
        P.info('Reading nim_showID')
    else:
        P.error('Failed reading nim_showID')


    
    #  Shot :
    nim_shot = h_root.userData("nim_shot")
    if nim_shot is not None:
        nim.set_name( elem='shot', name=nim_shot )
        P.info('Reading nim_shot')
    else:
        P.error('Failed reading nim_shot')


    
    #  Shot ID :
    nim_shotID = h_root.userData("nim_shotID")
    if nim_shotID is not None:
        nim.set_ID( elem='shot', ID=nim_shotID )
        P.info('Reading nim_shotID')
    else:
        P.error('Failed reading nim_shotID')


    
    #  Asset :
    nim_asset = h_root.userData("nim_asset")
    if nim_asset is not None:
        nim.set_name( elem='asset', name=nim_asset )
        P.info('Reading nim_asset')
    else:
        P.error('Failed reading nim_asset')

    
    #  Asset ID :
    nim_assetID = h_root.userData("nim_assetID")
    if nim_assetID is not None:
        nim.set_ID( elem='asset', ID=nim_assetID )
        P.info('Reading nim_assetID')
    else:
        P.error('Failed reading nim_assetID')

    
    #  File ID :
    nim_fileID = h_root.userData("nim_fileID")
    if nim_fileID is not None:
        nim.set_ID( elem='file', ID=nim_fileID )
        P.info('Reading nim_fileID')
    else:
        P.error('Failed reading nim_fileID')

    
    #  Shot/Asset Name :
    nim_name = h_root.userData("nim_name")
    if nim_name is not None:
        if nim.tab()=='SHOT' :
            P.debug( 'Shot Name = %s' % nim_name )
            #nim.set_tab( nim_name.Get() )
        elif nim.tab()=='ASSET' :
            P.debug( 'Asset Name = %s' % nim_name )
            #nim.set_tab( nim_name.Get() )
    else:
        P.error('Failed reading nim_name')



    #  Basename :
    nim_basename = h_root.userData("nim_basename")
    if nim_basename is not None:
        nim.set_name( elem='base', name=nim_basename )
        P.info('Reading nim_basename')
    else:
        P.error('Failed reading nim_basename')



    #  Task :
    nim_type = h_root.userData("nim_type")
    if nim_type is not None:
        nim.set_name( elem='task', name=nim_type )
        P.info('Reading nim_type')
    else:
        P.error('Failed reading nim_type')



    #  Task ID :
    nim_typeID = h_root.userData("nim_typeID")
    if nim_typeID is not None:
        nim.set_ID( elem='task', ID=nim_typeID )
        P.info('Reading nim_typeID')
    else:
        P.error('Failed reading nim_typeID')


    
    #  Task Folder :
    nim_typeFolder = h_root.userData("nim_typeFolder")
    if nim_typeFolder is not None:
        nim.set_taskFolder( folder=nim_typeFolder )
        P.info('Reading nim_typeFolder')
    else:
        P.error('Failed reading nim_typeFolder')

    
    #  Tag :
    nim_tag = h_root.userData("nim_tag")
    if nim_tag is not None:
        nim.set_name( elem='tag', name=nim_tag )
        P.info('Reading nim_tag')
    else:
        P.error('Failed reading nim_tag')

    
    #  File Type :
    nim_fileType = h_root.userData("nim_fileType")
    if nim_fileType is not None:
        nim.set_name( elem='file', name=nim_fileType )
        P.info('Reading nim_fileType')
    else:
        P.error('Failed reading nim_fileType')

    #  Print dictionary :
    #P.info('\nNIM Dictionary from get vars...')
    #nim.Print()
    
    return
    

def mk_workspace( proj_folder='', renPath='' ) :
    'Creates the NIM Project Workspace'

    proj_folder = ''

    workspace='\n'
    workspace='[Directories]\n'
    workspace +='Animations=./sceneassets/animations\n'
    workspace +='Archives=./archives\n'
    workspace +='AutoBackup=./autoback\n'
    workspace +='BitmapProxies=./proxies\n'
    workspace +='Downloads=./downloads\n'
    workspace +='Export=./export\n'
    workspace +='Expressions=./express\n'
    workspace +='Images=./sceneassets/images\n'
    workspace +='Import=./import\n'
    workspace +='Materials=./materiallibraries\n'
    workspace +='MaxStart=./scenes\n'
    workspace +='Photometric=./sceneassets\photometric\n'
    workspace +='Previews=./previews\n'

    workspace +='ProjectFolder='+proj_folder+'\n'

    workspace +='RenderAssets=./sceneassets/renderassets\n'
    
    #  Add render images directory :
    if not renPath :
        workspace +='RenderOutput=./renderoutput\n'
    else :
        renPath=renPath.replace('\\', '/')
        workspace +='RenderOutput='+renPath+'\n'

    workspace +='RenderPresets=./renderpresets\n'
   
    workspace +='Scenes=./scenes\n'
    workspace +='Sounds=./sceneassets/sound\n'
    workspace +='VideoPost=./vpost\n'
    workspace +='[XReferenceDirs]\n'
    workspace +='Dir1=./scenes\n'

    #TODO: UPDATE WITH ACTIVE BITMAP DIRS
    workspace +='[BitmapDirs]\n'
    workspace +='Dir1=C:/Program Files/Autodesk/3ds Max 2016/Maps\n'
    workspace +='Dir2=C:/Program Files/Autodesk/3ds Max 2016/Maps/glare\n'
    workspace +='Dir3=C:/Program Files/Autodesk/3ds Max 2016/Maps/adskMtl\n'
    workspace +='Dir4=C:/Program Files/Autodesk/3ds Max 2016/Maps/Noise\n'
    workspace +='Dir5=C:/Program Files/Autodesk/3ds Max 2016/Maps/Substance\noises\n'
    workspace +='Dir6=C:/Program Files/Autodesk/3ds Max 2016/Maps/Substance\textures\n'
    workspace +='Dir7=C:/Program Files/Autodesk/3ds Max 2016/Maps/mental_mill\n'
    workspace +='Dir8=C:/Program Files/Autodesk/3ds Max 2016/Maps/fx\n'
    workspace +='Dir9=C:/Program Files/Autodesk/3ds Max 2016/Maps/Particle Flow Presets\n'
    workspace +='Dir10=./downloads\n'

    return workspace
    

def mk_proj( path='', renPath='' ) :
    'Creates a show project structure'
    import hou
    workspaceExists=False
    
    #  Variables :
    projDirs=['abc','audio', 'comp', 'desk', 'flip', 'geo',
        'hda', 'render', 'scripts', 'sim', 'tex', 'video']
    
    projectName = os.path.basename(os.path.normpath(path))
    P.info('Project Folder: %s' % projectName)

    '''
    # DEPRECATED: we dont craete projects relatives to $HIP anymore.
    # Use project publishing structure instead
    #  Create Houdini project directories :
    if os.path.isdir( path ) :
        for projDir in projDirs:
            _dir=os.path.normpath( os.path.join( path, projDir ).replace('\\', '/') )
            if not os.path.isdir( _dir ) :
                P.info("DIR: %s" % _dir)
                try : os.mkdir( _dir )
                except Exception, e :
                    P.error( 'Failed creating the directory: %s' % _dir )
                    P.error( '    %s' % traceback.print_exc() )
                    return False
    '''
    
    '''
    #  Check for workspace file :
    projectConfigFileName = projectName+'.mxp'
    workspaceFile=os.path.normpath( os.path.join( path, projectConfigFileName ) )
    if os.path.exists( workspaceFile ) :
        workspaceExists=True
    
    #  Create workspace file :
    if not workspaceExists :
        P.info('Creating Houdini path configuration file...')
        workspace_text=mk_workspace( projectName, renPath )
        workspace_file=open( workspaceFile, 'w' )
        workspace_file.write( workspace_text )
        workspace_file.close
    
        #  Write out the render path :
        if renPath and os.path.isdir( renPath ) :
            try :
                nim_file=open( os.path.join( path, 'nim.mel' ), 'w' )
                nim_file.write( renPath )
                nim_file.close
            except : P.info( 'Sorry, unable to write the nim.mel file' )
    '''

    #  Set Project :
    try :
        pathToSet=path.replace('\\', '/')+'/'
        if os.path.isdir( pathToSet ) :
            # update the environment variables
            os.environ.update({"JOB": str(pathToSet)})
            # update JOB using hscript
            hou.hscript("set -g JOB = '" + str(pathToSet) + "'")
            hou.allowEnvironmentToOverwriteVariable("JOB", True)
            P.info( 'Current Project Set: %s\n' % pathToSet )
        else :
            P.info('Project not set!')
    except : pass
    
    return True
    



#  End
