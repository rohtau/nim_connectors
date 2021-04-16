#!/usr/bin/env python
#******************************************************************************
#
# Filename: nim_file.py
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
import os, platform, re, shutil, stat, traceback, sys, time
#  NIM Imports :
if sys.version_info >= (3,0):
    from . import nim_api as Api
    from . import nim_print as P
    from . import nim_win as Win
    from . import nim as Nim
else:
    import nim_api as Api
    import nim_print as P
    import nim_win as Win
    import nim as Nim
    
from imp import reload


#  Variables :
# version='v4.0.61'
# winTitle='NIM_'+version
from .import version 
from .import winTitle
_os=platform.system().lower()
#  Compiled REGEX Searches :
ext_srch=re.compile( '\.[a-zA-Z0-9]+$' )
end_srch=re.compile( '_[vV]?[0-9]+(_PUB)?\.[a-zA-Z0-9]+$' )
num_srch=re.compile( '[0-9]+' )


def get_user() :
    'Retrieves the current user\'s username'
    # TODO : Check if this function can be removed as redundant
    #  Get username :
    if os.getenv( 'USER' ) :
        _usr=os.getenv( 'USER' )
    elif os.getenv( 'USERNAME' ) :
        _usr=os.getenv( 'USERNAME' )
    if _usr :
        return _usr
    else :
        return False

def get_app() :
    'Gets the application by attempting various import statements'
    # TODO: Check if this function can be removed as redundant
    try :
        import maya.cmds as mc
        return 'Maya'
    except :pass
    try :
        import nuke
        return 'Nuke'
    except : pass
    try :
        import c4d
        return 'C4D'
    except : pass
    try :
        import hiero.ui
        return 'Hiero'
    except : pass
    try :
        import MaxPlus
        return '3dsMax'
    except : pass
    try :
        import hou
        return 'Houdini'
    except : pass
    try:
        import cinesync
        return 'Cinesync'
    except: pass
    try :
        nim_app = os.environ.get('NIM_APP', '-1')
        if nim_app == 'Flame':
            return 'Flame'
    except: pass
    return None

def get_apps() :
    'Provides a list of supported applications'
    return ['Maya', 'Nuke', 'C4D', 'Hiero', '3dsMax', 'Houdini', 'Flame']

def get_ext( filePath='' ) :
    'Retrieves the extension of a given file'
    P.debug("get_ext:")
    global ext_srch
    ext_result=None
    
    if not filePath :
        filePath=get_filePath()
    if filePath :
        ext_result=ext_srch.search( filePath )
    if ext_result :
        P.debug("get_ext: ext_result = %s" % ext_result.group())
        return ext_result.group()
    else :
        app=get_app()
        P.debug("get_ext: App = %s" % app)

        if app=='Maya' :
            ext='.mb'
        elif app=='Nuke' :
            import nuke
            if nuke.env['nc'] :
                ext = '.nknc'
            else :
                ext='.nk'
        elif app=='C4D' :
            ext='.c4d'
        elif app=='Hiero' :
            ext='.hrox'
        elif app=='3dsMax' :
            ext='.max'
        elif app=='Houdini' :
            ext='.hip'
        elif app=='Flame' :
            ext='.batch'
        if ext :
            return ext
        else :
            return False

def get_ver( filePath='' ) :
    'Retrieves the version number of a file'
    global end_srch, num_srch
    ext=get_ext( filePath )

    #  Derive version number :
    end_result=end_srch.search( filePath )
    if end_result :
        num_result=num_srch.search( end_result.group()[:-1*len(ext)] )
        if num_result :
            return int(num_result.group())
    else :
        return 1

def get_filePath() :
    'Retrieves the file path from the current application'
    filePath=''
    
    #  Maya :
    try :
        import maya.cmds as mc
        filePath=mc.file( query=True, sn=True )
    except : pass
    #  Nuke :
    if not filePath :
        try :
            import nuke
            P.debug("get_filePath: Nuke Found")     #WILL NEED TO DETERMINE IF NUKE STUDIO AND TRYING TO SAVE PROJECT
            filePath=nuke.root().name()
        except : pass
    #  Hiero :
    if not filePath :
        try :
            import hiero.core
            P.debug("get_filePath: Hiero Found")
            projects=hiero.core.projects()
            filePath=projects[0].path()
        except : pass
    #  C4D :
    if not filePath :
        try :
            import c4d
            filePath=''
            doc=c4d.documents.GetActiveDocument()
            fileDir=doc.GetDocumentPath()
            fileName=doc.GetDocumentName()
            if fileDir and fileName :
                filePath=os.path.join( fileDir, fileName )
        except : pass
    #   3dsMax :
    if not filePath :
        try :
            import MaxPlus
            P.debug("get_filePath: 3dsMax Found")
            fm = MaxPlus.FileManager
            filePath=fm.GetFileNameAndPath()
        except : pass
    #   Houdini :
    if not filePath :
        try :
            import hou
            P.debug("get_filePath: Houdini Found")
            filePath=hou.hipFile.name()
        except : pass

    #  Return :
    if filePath :
        return os.path.normpath( filePath )
    else :
        return False

def os_filePath( path='', nim=None, serverID=None ) :
    'Returns the platform specific path to a filepath.'
    filePath, fp_noServer, server='', '', ''
    
    #P.info("os_filePath PATH: %s" % path)
    #  Error Checking :
    if not nim.ID('job') :
        P.warning('Unable to find a platform specific OS path')
        return path

    if not serverID :
        serverDict=Api.get_serverInfo( nim.server(get='ID') )
    else :
        serverDict=Api.get_serverInfo( serverID )
    #P.info("serverDict: %s" % serverDict)

    if not serverDict or not len(serverDict) :
        P.warning('Unable to find a platform specific OS path')
        return path
    
    if nim.server() :
        fp_noServer=path[len(nim.server()):]

    # The following removed - redundant
    '''
    if nim.tab()=='SHOT' :
        serverDict=Api.get_jobServers( nim.ID('job') )
    elif nim.tab()=='ASSET' :
        serverDict=Api.get_jobServers( nim.ID('job') )
    '''
    
    #if serverDict and len(serverDict)>0 :      # removed to only compare to single server  
    if serverDict and len(serverDict)==1 :      # failed if more than one server found in serverDict

        #  Substitute Windows Paths :
        if serverDict[0]['winPath']:
            #P.info('Reading Window Path...')
            if re.search( '^'+serverDict[0]['winPath'], path ) :
                fp_noServer=path[len(serverDict[0]['winPath']):]
            elif re.search( '^'+serverDict[0]['winPath'], path.replace('\\', '/') ) :
                fp_noServer=path[len(serverDict[0]['winPath']):]
            elif re.search( '^'+serverDict[0]['winPath'], path.replace('/', '\\') ) :
                fp_noServer=path[len(serverDict[0]['winPath']):]
        
        #  Substitute Mac paths :
        if serverDict[0]['osxPath']:
            #P.info('Reading OSX Path...')
            if re.search( '^'+serverDict[0]['osxPath'], path ) :
                fp_noServer=path[len(serverDict[0]['osxPath']):]
            elif re.search( '^'+serverDict[0]['osxPath'], path.replace('\\', '/') ) :
                fp_noServer=path[len(serverDict[0]['osxPath']):]
            elif re.search( '^'+serverDict[0]['osxPath'], path.replace('/', '\\') ) :
                fp_noServer=path[len(serverDict[0]['osxPath']):]
        
        #  Substitute Linux Paths :
        if serverDict[0]['path']:
            #P.info('Reading Linux Path...')
            if re.search( '^'+serverDict[0]['path'], path ) :
                fp_noServer=path[len(serverDict[0]['path']):]
            elif re.search( '^'+serverDict[0]['path'], path.replace('\\', '/') ) :
                fp_noServer=path[len(serverDict[0]['path']):]
            elif re.search( '^'+serverDict[0]['path'], path.replace('/', '\\') ) :
                fp_noServer=path[len(serverDict[0]['path']):]
        
        #  Store file path :
        if _os.lower() in ['windows', 'win32'] :
            server=serverDict[0]['winPath']
            path=server+fp_noServer
            filePath=path.replace('/', '\\')
            return filePath
        elif _os.lower() in ['darwin', 'mac'] :
            server=serverDict[0]['osxPath']
            path=server+fp_noServer
            filePath=path.replace('\\', '/')
            return filePath
        elif _os.lower() in ['linux', 'linux2'] :
            server=serverDict[0]['path']
            path=server+fp_noServer
            filePath=path.replace('\\', '/')
            return filePath
        else :
            P.info( 'Operating system, %s, not in valid list of operating systems' %_os )
            return False
        
        P.info( 'Filepath set to - %s' % filePath )
    
    else :
        P.error('Unable to convert filepath by platform!')
        return False
    
    return filePath

#DEPRECATED
def task_toAbbrev( task='' ) :
    'Returns the short version of a given task' 
    return_task=task
    '''
    if task in ['MODEL', 'Model', 'model'] :
        return_task='MOD'
    elif task in ['RIGGING', 'Rigging', 'rigging', 'RIG', 'Rig', 'rig'] :
        return_task='RIG'
    elif task in ['TEXTURE', 'Texture', 'texture'] :
        return_task='SHD'
    elif task in ['REFERENCE', 'Reference', 'reference', 'REF', 'Ref', 'ref'] :
        return_task='REF'
    '''
    return return_task

def elementType_toAbbrev( elem ):
    'Returns the short version for some element types'
    if not elem:
        return ""
    if elem == 'plates':
        return 'plate'
    if elem == 'renders':
        return 'cg'
    elif elem == 'comps' or elem == 'comp':
        return '2d'
        # return '2d'
    else:
        return elem
    pass


def verUpSaveFile( filepath, nim, projpath='', selected=False, pub=False, symLink=True ) :
    '''
    Save the new version file on the file system.
    It can also create the project dirs for various apps

    Arguments:
        filepath {str} -- Path to new file
        nim {nim object} -- NIM object with all the publishing information

    Keyword Arguments:
        projpath {str} -- path to project. If empty no project will be created.
        selected {bool} -- Whether or not to save only selected (default: {False})
        pub {bool} -- Whether or not to publish file (default: {False})
        symLink {bool} -- Use symlinks when publishing (default: {True})

    Returns:
        [str] -- path to new file
    '''

    #  Directories :
    #===---------------
    
    #  Make basename directory :
    if projpath and not os.path.isdir( projpath ) :
        P.info( 'Creating basename directory within...\n    %s' % projpath )
        og_umask=os.umask(0)
        os.makedirs( projpath )
        os.umask(og_umask)
        if os.path.isdir( projpath ) :
            P.info( '  Successfully created the basename directory!' )
        else :
            P.warning( '  Unable to create basename directory' )
    
    #  Make render directory :
    renDir = nim.renderPath()
    if renDir and not os.path.isdir( renDir ) :
        P.info( 'Creating render directory...\n      %s' % renDir )
        
        og_umask=os.umask(0)
        os.makedirs( renDir )
        os.umask(og_umask)
        
        if os.path.isdir( renDir ) :
            P.info( '    Successfully created the render directory!' )
        else :
            P.warning( '    Unable to create project directories.' )
    elif renDir :
        P.debug( 'Render directory already exists.\n' )
    
    #  Make Maya Project directory :
    if os.path.isdir( projpath ) and nim.app()=='Maya' :
        import nim_maya as M
        if M.makeProject( projectLocation=projpath, renderPath=renDir ) :
            P.info( 'Created Maya project directorires within...\n    %s' % projpath )
        else :
            P.warning( '    Unable to create Maya project directories.' )
    elif nim.app()=='Maya' :
        P.warning( 'Didn\'t create Maya project directories.' )

    #  Make 3dsMax Project directory :
    if os.path.isdir( projpath ) and nim.app()=='3dsMax' :
        import nim_3dsmax as Max
        if Max.mk_proj( path=projpath, renPath=renDir ) :
            P.info( 'Created 3dsMax project directorires within...\n    %s' % projpath )
        else :
            P.warning( '    Unable to create 3dsMax project directories.' )
    elif nim.app()=='3dsMax' :
        P.warning( 'Didn\'t create 3dsMax project directories.' )

    #  Make Houdini Project directory :
    # TODO: this wil be removed
    if os.path.isdir( projpath ) and nim.app()=='Houdini' :
        import nim_houdini as Houdini
        if Houdini.mk_proj( path=projpath, renPath=renDir ) :
            P.info( 'Created Houdini project directorires within...\n    %s' % projpath )
        else :
            P.warning( '    Unable to create Houdini project directories.' )
    elif nim.app()=='Houdini' :
        P.warning( 'Didn\'t create Houdini project directories.' )
    
    
    #  Save :
    #===------
    P.info('APP = %s' % nim.app())
    filename = os.path.basename( filepath )

    #  Maya :
    if nim.app()=='Maya' :
        import maya.cmds as mc
        
        #  Save File :
        if not selected :
            #  Set Vars :
            import nim_maya as M
            M.set_vars( nim=nim )
            
            P.info( 'Saving file as %s \n' % filepath )
            mc.file(rename=filepath)
            if ext=='.mb' :
                mc.file( save=True, type='mayaBinary' )
            elif ext=='.ma' :
                mc.file( save=True, type='mayaAscii' )
        else :
            P.info( 'Saving selected items as %s \n' % filepath )
            if ext=='.mb' :
                mc.file( filepath, exportSelected=True, type='mayaBinary' )
            elif ext=='.ma' :
                mc.file( filepath, exportSelected=True, type='mayaAscii' )
    
    #  Nuke :
    elif nim.app()=='Nuke' :
        
        import nuke
        
        #  Save File :
        if not selected :
            #  Set Vars :
            import nim_nuke as N
            N.set_vars( nim=nim )
            P.info( 'Saving file as %s \n' % filepath )
            nuke.scriptSaveAs( filepath )
        elif selected :
            P.info( 'Saving selected items as %s \n' % filepath )
            try :
                nuke.nodeCopy( filepath )
            except RuntimeError:
                P.info( 'Failed to selected items... Possibly no items selected.' )
                return False

    
    #  Cinema 4D :
    elif nim.app()=='C4D' :
        import c4d
        
        #  Set Vars :
        nim_plugin_ID=1032427
        
        #  Save File :
        if not selected :
            P.info( 'Saving file as %s \n' % filepath )
            import nim_c4d as C
            C.set_vars( nim=nim, ID=nim_plugin_ID )
            doc=c4d.documents.GetActiveDocument()
            doc.SetDocumentName( filename )
            doc.SetDocumentPath( fileDir )
            c4d.documents.SaveDocument( doc, str(filepath),
                c4d.SAVEDOCUMENTFLAGS_DIALOGSALLOWED,
                c4d.FORMAT_C4DEXPORT )
            P.info( 'Saving File Complete')
        #  Save Selected :
        else :
            P.info( 'Saving selected items as %s \n' % filepath )
            doc=c4d.documents.GetActiveDocument()
            sel=doc.GetActiveObjects( False )
            baseDoc=c4d.documents.IsolateObjects(doc, sel)
            c4d.documents.SaveDocument( baseDoc, str(filepath),
                c4d.SAVEDOCUMENTFLAGS_DIALOGSALLOWED,
                c4d.FORMAT_C4DEXPORT)
    
    #  Hiero :
    elif nim.app()=='Hiero' :
        import hiero.core
        projects=hiero.core.projects()
        proj=projects[0]
        curFilePath=proj.path()
        proj.saveAs( filepath )
        #proj=hiero.core.project( projName )
        #proj=hiero.core.Project
        #proj=self._get_current_project()
    
    #  3dsMax :
    if nim.app()=='3dsMax' :
        import MaxPlus
        maxFM = MaxPlus.FileManager
        #  Save File :
        if not selected :
            #  Set Vars :
            import nim_3dsmax as Max
            Max.set_vars( nim=nim )
            #Save File
            P.info( 'Saving file as %s \n' % filepath )
            maxFM.Save(filepath)
        else :
            #Save Selected Items
            P.info( 'Saving selected items as %s \n' % filepath )
            maxFM.SaveSelected(filepath)

    #  Houdini :
    if nim.app()=='Houdini' :
        import hou
        #  Save File :
        if not selected :
            #  Set Vars :
            import nim_houdini as Houdini
            Houdini.set_vars( nim=nim )
            #Save File
            if _os.lower() in ['windows', 'win32'] :
                hipFilePath = filepath.replace('\\','/')
            P.info( 'Saving file as %s \n' % hipFilePath )
            hou.hipFile.save(file_name=str(hipFilePath))
            #Set $HIP var to location of current file
            if _os.lower() in ['windows', 'win32'] :
                hipProj = projpath.replace('\\','/')
            hou.hscript("set -g HIP = '" + str(hipProj) + "'")
            #Set $HIPNAME var to current file
            hipName = os.path.splitext(filename)[0]
            hou.hscript("set -g HIPNAME = '" + str(hipName) + "'")
        else :
            #Save Selected Items
            #TODO: set to saveSelect items... currently saving entire scene
            if _os.lower() in ['windows', 'win32'] :
                hipFilePath = filepath.replace('\\','/')
            P.info( 'Saving selected items as %s \n' % hipFilePath )
            hou.hipFile.save(file_name=str(hipFilePath))
            #Set $HIP var to location of current file
            if _os.lower() in ['windows', 'win32'] :
                hipProj = projpath.replace('\\','/')
            hou.hscript("set -g HIP = '" + str(hipProj) + "'")
            #Set $HIPNAME var to current file
            hipName = os.path.splitext(filename)[0]
            hou.hscript("set -g HIPNAME = '" + str(hipName) + "'")

    #  Make a copy of the file, if publishing :
    if pub and not symLink :
        pub_fileName=basename+ext
        pub_fileDir=Api.to_nimDir( nim=nim )
        pub_filePath=os.path.join( pub_fileDir, pub_fileName )
        #  Delete any pre-existing published file :
        if os.path.isfile( pub_filePath ) :
            os.chmod( pub_filePath, stat.S_IWRITE )
            os.remove( pub_filePath )
        #  Copy fiile and make it read-only :
        shutil.copyfile( filepath, pub_filePath )
        os.chmod( pub_filePath, stat.S_IREAD )
        
    #  Print save success :
    P.info( '\nFile successfully saved to...\n    %s\n' % filepath )
    return filepath


# selected can be removed or deprecated
def verUp( nim=None, padding=2, selected=False, win_launch=False, pub=False, symLink=True ) :
    '''
    Versions up a file - Does NOT add it to the NIM API. 
    Work out new file path and projDir, but not save any file and not create anything in the file system.
    That is for verUpsaveFile()

    Keyword Arguments:
        nim      {nim Dict}: NIM dictionarywit publishing info (default: {None})
        padding  {int}     : Version number padding (default: {2})
        selected {bool}    : Whether or not save only selected (default: {False})
        pub      {bool}    : Is this a publishing (default: {False})
        symLink  {bool}    : Whether or not do symlink when publishing (default: {True})

    Returns:
        dict : {'filepath':new_filePath, 'projpath':projDir, 'nim':nim}

    '''

    # print("DEBUG: In File Ver Up")
    
    #  Variables :
    cur_filePath, cur_fileDir, cur_fileName='', '', ''
    scenePath, assetName, shotName='', '', ''
    server, fileBase, nimDir, fileDir, ext, verNum='', '', '', '', '', None
    renDir, compPath='', ''
    
    #  Get current file information :
    if not nim :
        #  Initialize NIM dictionary :
        nim=Nim.NIM()
        nim.ingest_prefs()
        if pub : nim.set_name( elem='filter', name='Published' )
        else : nim.set_name( elem='filter', name='Work' )
    

    #P.info("SERVER ID: %s" % str(nim.server(get='ID')))
    # Get Server OS Path from server ID
    serverOsPathInfo = Api.get_serverOSPath( nim.server(get='ID'), platform.system() )
    P.info("Server OS Path: %s" % serverOsPathInfo)
    serverOSPath = serverOsPathInfo[0]['serverOSPath']
    nim.set_server( path=serverOSPath )


    #  Attempt to get current file information :
    if nim.filePath() :
        cur_filePath=nim.filePath()
        cur_fileDir=nim.fileDir()
        cur_fileName=nim.fileName()
    
    #  Basename :
    nim.set_name( elem='base', name=Api.to_basename( nim=nim ) )
    basename=nim.name('base')
    
    #  Directory to save to :
    api_fileDir=Api.to_fileDir( nim )
    if api_fileDir and not cur_fileDir :
        fileDir=api_fileDir
    elif not api_fileDir and cur_fileDir :
        fileDir=cur_fileDir
    elif api_fileDir and cur_fileDir :
        fileDir=api_fileDir
   
    #  Project Directory :
    #XXX: What?? This scenes folder is hardcoded???
    # if fileDir[-6:]=='scenes' : projDir=fileDir[:-6]
    # else : projDir=fileDir
    # This add support to create project folders correctly according with supported scene folder names.
    # If the base name is recognisedd as a scene name then the project folder will be it's parent, otherwise
    # create projects at the same level as the scenes.
    scenefolder = os.path.basename(fileDir)
    if scenefolder in ('scenes', 'hip'):
        projDir = os.path.dirname( fileDir )
    else:
        projDir = fileDir
    
    #  Convert file directory :
    #P.info("fileDir: %s" % fileDir)
    fileDir=os_filePath( path=fileDir, nim=nim )
    P.info( 'File Directory = %s' %  fileDir )
    projDir=os_filePath( path=projDir, nim=nim )
    P.info( 'Project Directory = %s' %  projDir )
    
    #  Version Number :
    baseInfo=''
    if nim.tab()=='SHOT' :
        baseInfo=Api.get_baseVer( shotID=nim.ID('shot'), basename=nim.name('base') )
    elif nim.tab()=='ASSET' :
        baseInfo=Api.get_baseVer( assetID=nim.ID('asset'), basename=nim.name('base') )
    if baseInfo :
        ver_baseInfo=baseInfo[0]['version']
        verNum=int(ver_baseInfo)+1
    else :
        verNum=1
    try :
        for f in [f for f in os.listdir(fileDir) if os.path.isfile(os.path.join(fileDir, f))] :
            verSrch=re.search( basename+'_v[0-9]+', f )
            if verSrch :
                numSrch=re.search( '[0-9]+$', verSrch.group() )
                if numSrch :
                    if int(numSrch.group()) >verNum :
                        verNum=int(numSrch.group())
    except : pass

    nim.set_version( version=str(verNum) )
    
    #  Set Extension :
    ext=nim.name('fileExt')
    if not ext :
        P.debug('Getting Extension')
        ext=get_ext()

    P.debug('Extension = %s' % ext)
    
    #  Error Checking :
    if not fileDir or not basename :
        msg='Sorry, you must either: Save the file from the NIM File GUI, or\n'+\
            '    save the file in the appropriate folders, with the correct name.\n\n'+\
            'File NOT saved.'
        P.error( msg )
        Win.popup( title='NIM - Version Up Error', msg=msg )
        return False

    #  Construct new File Name :
    '''
    if not pub :
        new_fileName='%s_v%s%s' % ( basename, str(verNum).zfill(int(padding)), ext )
    elif pub :
        verNum -=1
        new_fileName='%s_v%s_PUB%s' % ( basename, str(verNum).zfill(int(padding)), ext )
    '''
    # Use our convention with __ to separate fields in the file name:
    if not pub :
        new_fileName='%s__v%s%s' % ( basename, str(verNum).zfill(int(padding)), ext )
    elif pub :
        verNum -=1
        new_fileName='%s__v%s__PUB%s' % ( basename, str(verNum).zfill(int(padding)), ext )
    
    
    #  Construct new File Path :
    temp_filePath=os.path.normpath( os.path.join( fileDir, new_fileName ) )
    new_filePath=os_filePath( path=temp_filePath, nim=nim )
    
    #  Construct Render Directory :
    if nim.tab()=='SHOT' and nim.ID('shot') :
        pathInfo=Api.get( {'q': 'getPaths', 'type': 'shot', 'ID' : str(nim.ID('shot'))} )
    elif nim.tab()=='ASSET' and nim.ID('asset') :
        pathInfo=Api.get( {'q': 'getPaths', 'type': 'asset', 'ID' : str(nim.ID('asset'))} )
    if pathInfo and type(pathInfo)==type(dict()) and 'renders' in pathInfo :
        renDir=os.path.normpath( os.path.join( nim.server(), pathInfo['renders'] ) )
        # Add render path to nim object
        nim.set_renderPath( renderPath=renDir)
    else :
        #  Use old method, if path information can't be derived :
        renDir=Api.to_renPath( nim )
        nim.set_renderPath( renderPath=renDir)
    renDir=os_filePath( path=renDir, nim=nim )
    
    #  Comp Path :
    if pathInfo and type(pathInfo)==type(dict()) and 'comps' in pathInfo :
        compPath=os.path.normpath( os.path.join( nim.server(), pathInfo['comps'] ) )
        nim.set_compPath( compPath=compPath )
    compPath=os_filePath( path=compPath, nim=nim )
    
    #  Add Plates Path :
    if pathInfo and type(pathInfo)==type(dict()) and 'comps' in pathInfo :
        platesPath=os.path.normpath( os.path.join( nim.server(), pathInfo['plates'] ) )
        nim.set_platesPath( platesPath=platesPath )
    platesPath=os_filePath( path=platesPath, nim=nim )

    # Add job ans shot/asset path
    if pathInfo and type(pathInfo)==type(dict()) and 'root' in pathInfo :
        shotPath=os.path.normpath( os.path.join( nim.server(), pathInfo['root'] ) )
        nim.set_shotPath( shotPath=shotPath )

    # jobpath = os.path.normpath(os.path.join(serverOsPathInfo, nim.Dict(elem='job')['name']))
    nimdict = nim.get_nim()
    if 'job' in nimdict:
        jobpath = os.path.normpath(os.path.join(os.path.normpath(serverOSPath), nimdict['job']['name'].split()[0]))
        nim.set_jobPath( jobPath=jobpath )

    P.info( '\nVariables:' )
    P.info( '  Initial File Path = %s' % cur_filePath )
    P.info( '  Basename = %s' % basename )
    P.info( '  Project Directory = %s' % projDir )
    P.info( '  New File Path = %s' % new_filePath )
    P.info( '  Render Directory = %s' % renDir )
    P.info( '  Comp Directory = %s\n' % compPath )
    P.info( '  Plates Directory = %s\n' % platesPath )

    # TODO: check that file path and projDir are writable
    
    '''
    #  Directories :
    #===---------------
    
    #  Make basename directory :
    if projDir and not os.path.isdir( projDir ) :
        P.info( 'Creating basename directory within...\n    %s' % projDir )
        og_umask=os.umask(0)
        os.makedirs( projDir )
        os.umask(og_umask)
        if os.path.isdir( projDir ) :
            P.info( '  Successfully created the basename directory!' )
        else :
            P.warning( '  Unable to create basename directory' )
    
    #  Make render directory :
    if renDir and not os.path.isdir( renDir ) :
        P.info( 'Creating render directory...\n      %s' % renDir )
        
        og_umask=os.umask(0)
        os.makedirs( renDir )
        os.umask(og_umask)
        
        if os.path.isdir( renDir ) :
            P.info( '    Successfully created the render directory!' )
        else :
            P.warning( '    Unable to create project directories.' )
    elif renDir :
        P.debug( 'Render directory already exists.\n' )
    
    #  Make Maya Project directory :
    if os.path.isdir( projDir ) and nim.app()=='Maya' :
        from . import nim_maya as M
        if M.makeProject( projectLocation=projDir, renderPath=renDir ) :
            P.info( 'Created Maya project directorires within...\n    %s' % projDir )
        else :
            P.warning( '    Unable to create Maya project directories.' )
    elif nim.app()=='Maya' :
        P.warning( 'Didn\'t create Maya project directories.' )

    #  Make 3dsMax Project directory :
    if os.path.isdir( projDir ) and nim.app()=='3dsMax' :
        from . import nim_3dsmax as Max
        if Max.mk_proj( path=projDir, renPath=renDir ) :
            P.info( 'Created 3dsMax project directorires within...\n    %s' % projDir )
        else :
            P.warning( '    Unable to create 3dsMax project directories.' )
    elif nim.app()=='3dsMax' :
        P.warning( 'Didn\'t create 3dsMax project directories.' )

    #  Make Houdini Project directory :
    # TODO: this wil be removed
    if os.path.isdir( projDir ) and nim.app()=='Houdini' :
        from . import nim_houdini as Houdini
        if Houdini.mk_proj( path=projDir, renPath=renDir ) :
            P.info( 'Created Houdini project directorires within...\n    %s' % projDir )
        else :
            P.warning( '    Unable to create Houdini project directories.' )
    elif nim.app()=='Houdini' :
        P.warning( 'Didn\'t create Houdini project directories.' )
    
    
    #  Save :
    #===------
    P.info('APP = %s' % nim.app())

    #  Maya :
    if nim.app()=='Maya' :
        import maya.cmds as mc
        
        #  Save File :
        if not selected :
            #  Set Vars :
            from . import nim_maya as M
            M.set_vars( nim=nim )
            
            P.info( 'Saving file as %s \n' % new_filePath )
            mc.file(rename=new_filePath)
            if ext=='.mb' :
                mc.file( save=True, type='mayaBinary' )
            elif ext=='.ma' :
                mc.file( save=True, type='mayaAscii' )
        else :
            P.info( 'Saving selected items as %s \n' % new_filePath )
            if ext=='.mb' :
                mc.file( new_filePath, exportSelected=True, type='mayaBinary' )
            elif ext=='.ma' :
                mc.file( new_filePath, exportSelected=True, type='mayaAscii' )
    
    #  Nuke :
    elif nim.app()=='Nuke' :
        
        import nuke
        
        #  Save File :
        if not selected :
            #  Set Vars :
            from . import nim_nuke as N
            N.set_vars( nim=nim )
            P.info( 'Saving file as %s \n' % new_filePath )
            nuke.scriptSaveAs( new_filePath )
        elif selected :
            P.info( 'Saving selected items as %s \n' % new_filePath )
            try :
                nuke.nodeCopy( new_filePath )
            except RuntimeError:
                P.info( 'Failed to selected items... Possibly no items selected.' )
                return False

    
    #  Cinema 4D :
    elif nim.app()=='C4D' :
        import c4d
        
        #  Set Vars :
        nim_plugin_ID=1032427
        
        #  Save File :
        if not selected :
            P.info( 'Saving file as %s \n' % new_filePath )
            from . import nim_c4d as C
            C.set_vars( nim=nim, ID=nim_plugin_ID )
            doc=c4d.documents.GetActiveDocument()
            doc.SetDocumentName( new_fileName )
            doc.SetDocumentPath( fileDir )
            c4d.documents.SaveDocument( doc, str(new_filePath),
                c4d.SAVEDOCUMENTFLAGS_DIALOGSALLOWED,
                c4d.FORMAT_C4DEXPORT )
            P.info( 'Saving File Complete')
        #  Save Selected :
        else :
            P.info( 'Saving selected items as %s \n' % new_filePath )
            doc=c4d.documents.GetActiveDocument()
            sel=doc.GetActiveObjects( False )
            baseDoc=c4d.documents.IsolateObjects(doc, sel)
            c4d.documents.SaveDocument( baseDoc, str(new_filePath),
                c4d.SAVEDOCUMENTFLAGS_DIALOGSALLOWED,
                c4d.FORMAT_C4DEXPORT)
    
    #  Hiero :
    elif nim.app()=='Hiero' :
        import hiero.core
        projects=hiero.core.projects()
        proj=projects[0]
        curFilePath=proj.path()
        proj.saveAs( new_filePath )
        #proj=hiero.core.project( projName )
        #proj=hiero.core.Project
        #proj=self._get_current_project()
    
    #  3dsMax :
    if nim.app()=='3dsMax' :
        import MaxPlus
        maxFM = MaxPlus.FileManager
        #  Save File :
        if not selected :
            #  Set Vars :
            from . import nim_3dsmax as Max
            Max.set_vars( nim=nim )
            #Save File
            P.info( 'Saving file as %s \n' % new_filePath )
            maxFM.Save(new_filePath)
        else :
            #Save Selected Items
            P.info( 'Saving selected items as %s \n' % new_filePath )
            maxFM.SaveSelected(new_filePath)

    #  Houdini :
    if nim.app()=='Houdini' :
        import hou
        #  Save File :
        if not selected :
            #  Set Vars :
            from . import nim_houdini as Houdini
            Houdini.set_vars( nim=nim )
            #Save File
            if _os.lower() in ['windows', 'win32'] :
                hipFilePath = new_filePath.replace('\\','/')
            P.info( 'Saving file as %s \n' % hipFilePath )
            hou.hipFile.save(file_name=str(hipFilePath))
            #Set $HIP var to location of current file
            if _os.lower() in ['windows', 'win32'] :
                hipProj = projDir.replace('\\','/')
            hou.hscript("set -g HIP = '" + str(hipProj) + "'")
            #Set $HIPNAME var to current file
            hipName = os.path.splitext(new_fileName)[0]
            hou.hscript("set -g HIPNAME = '" + str(hipName) + "'")
        else :
            #Save Selected Items
            #TODO: set to saveSelect items... currently saving entire scene
            if _os.lower() in ['windows', 'win32'] :
                hipFilePath = new_filePath.replace('\\','/')
            P.info( 'Saving selected items as %s \n' % hipFilePath )
            hou.hipFile.save(file_name=str(hipFilePath))
            #Set $HIP var to location of current file
            if _os.lower() in ['windows', 'win32'] :
                hipProj = projDir.replace('\\','/')
            hou.hscript("set -g HIP = '" + str(hipProj) + "'")
            #Set $HIPNAME var to current file
            hipName = os.path.splitext(new_fileName)[0]
            hou.hscript("set -g HIPNAME = '" + str(hipName) + "'")

    #  Make a copy of the file, if publishing :
    if pub and not symLink :
        pub_fileName=basename+ext
        pub_fileDir=Api.to_nimDir( nim=nim )
        pub_filePath=os.path.join( pub_fileDir, pub_fileName )
        #  Delete any pre-existing published file :
        if os.path.isfile( pub_filePath ) :
            os.chmod( pub_filePath, stat.S_IWRITE )
            os.remove( pub_filePath )
        #  Copy file and make it read-only :
        shutil.copyfile( new_filePath, pub_filePath )
        os.chmod( pub_filePath, stat.S_IREAD )
        
    #  Print save success :
    P.info( '\nFile successfully saved to...\n    %s\n' % new_filePath )
    
    '''

    #  [AS]  returning nim object with current dictionary settings
    #return new_filePath
    return {'filepath':new_filePath, 'projpath':projDir, 'nim':nim}
    #  [AS]  END


def scripts_reload() :
    'Reloads the facility level scripts'
    try :
        from . import nim as Nim
        from . import nim_api as Api
        from . import nim_file as F
        from . import nim_prefs as Prefs
        from . import nim_print as P
        from . import nim_win as Win
        from . import nim_tools
        reload(Nim)
        reload(Api)
        reload(F)
        reload(Prefs)
        reload(P)
        reload(Win)
        reload(nim_tools)
        #  App specific modules :
        app=get_app()
        try :
            from . import UI as UI
            reload(UI)
        except : pass
        if app=='Maya' :
            from . import nim_maya as M
            reload(M)
        elif app=='Nuke' :
            from . import nim_nuke as N
            reload(N)
        elif app=='C4D' :
            from . import nim_c4d as C
            reload(C)
        elif app=='3dsMax' :
            from . import nim_3dsmax as Max
            reload(Max)
        elif app=='Houdini' :
            from . import nim_houdini as Houdini
            reload(Houdini)
        P.info( '    NIM scripts. have been reloaded.' )
    except Exception as e :
        print('Sorry, problem reloading scripts...')
        print('    %s' % traceback.print_exc())
    return


#  END
