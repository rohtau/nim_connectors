'''
File: nim_rohtau.py
Project: nim_core
File Created: Tuesday, 22nd December 2020 6:38:27 pm
Author: Pablo Gimenez (pablo@rohtau.com)
-----
Last Modified: Tuesday, 22nd December 2020 6:38:33 pm
Modified By: Pablo Gimenez (pablo@rohtau.com>)
-----
Copyright 2020 - 2020, rohtau
-----

rohtau interface with NIM and the publishing system in general.
Layer on yop of NIM shared across all supported apps in the pipeline
'''
import sys
import os
import platform
import re
import subprocess
import shlex
import time
import json
from subprocess import Popen
from datetime   import datetime
from pprint     import pprint
from pprint     import pformat
from builtins   import range

if sys.version_info >= (3,0):
    from . import nim                as Nim
    from . import nim_api            as nimAPI
    from . import nim_rohtau_utils   as nimUtl
    from . import nim_print          as nimP
else:
    import nim                as Nim
    import nim_api            as nimAPI
    import nim_rohtau_utils   as nimUtl
    import nim_print          as nimP

#  Variables :
from .import version 
from .import winTitle 
from .import padding 

#  Import Python GUI packages :
try : 
    from PySide2 import QtWidgets as QtGui
    from PySide2 import QtGui as QtGui2
    from PySide2 import QtCore
except ImportError :

    
    try : from PySide import QtCore, QtGui
    except ImportError :
        try : from PyQt4 import QtCore, QtGui
        except ImportError : 
            print("NIM: Failed to UI Modules - UI")

class pubOverwritePolicy:
    '''
    Enum for different publishing overwrite policies
    '''
    NOT_ALLOW  = 0
    ALLOW_USER = 1
    ALLOW_ALL  = 2

    pass
class pubState:
    '''
    Enum for different publishing data state

    Data State
    ----------
    Data  condition is defined in pub.pubState:
        class pubState:
            PENDING   = 0 # Data is being processed, not yet ready. For instance shot is still in render
            AVAILABLE = 1 # Data is ready and available
            ERROR     = 2 # There was an error and data is not healthy
            NA        = 2 # No Applicable, use for files that don't represent elements, like DCC scene files
            name      = ('Pending', 'Available', 'Error', 'N/A') # state names
    Usually data starts by default at PENDING, until processign has finished successfully. 
    If processing, rendering, is done correctly then status is changed to AVAILABLE
    If there is any error then it is changed to ERROR
    '''
    PENDING   = 0 # Data is being processed, not yet ready. For instance shot is still in render
    AVAILABLE = 1 # Data is ready and available
    ERROR     = 2 # There was an error and data is not healthy
    NA        = 3 # No Applicable, use for files that don't represent elements, like DCC scene files
    name      = ('Pending', 'Available', 'Error', 'N/A') # state names

    pass

def toPosix( path, force=False ):
    '''
    Convert path into Posix format.
    Remove drive letter and change \ to /

    Only does the conversion if platform is Windows, unless force is set
    in which case it is done in any platform.

    Arguments:
        path {str} -- source path
        force {bool} -- force conversion even for no Windows systems

    Returns:
        str -- path in Posix
    '''
    if platform.system() == 'Windows' or force:
        return re.sub('^\w:', '', path.replace('\\', '/') )
    else:
        return path

def openPath( path ):
    '''
    Cross platform function to open a path into platform's default app

    Parameters
    ----------
    path : str  
        Path to open

    Returns
    -------
    bool
        True if everything went fine
    '''
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        Popen(["open", path])
    else:
        Popen(["xdg-open", path])

    return True

def elementTypeFolder( elementtype, parent, parentID ):
    '''
    Based on an element type name or ID and a selected shot/asset return it's folder path.
    The path will be relative to the parent shot/asset
    The full path for the element type will be:
    [JOBPATH]/[work|build]/[SHOT|ASSET]/[ELEMENT]
    This function returns the ELEMENT portion, which in general is a folder name.

    Parameters
    ----------
    elementtype : str
        Element type name or ID
    parent : str
        Element parent item type: shot, asset or show
    parentID : int
        Element parent ID
    

    Returns
    -------
    str
        Element folder name. empty string if error
    '''
    folder = ""
    if len(elementtype) > 0:
        elmtsTypes = nimApi.get_elementTypes()
        pprint(elmtsTypes)
        if not elementtype.isnumeric():
            elementname = element
            for elm in elmtsTypes:
                if elm['ID'] == elementtype:
                    elementid = elm['ID']
                    break
        else:
            elementid = int(elementtype)
            for elm in elmtsTypes:
                if elm['name'] == elementtype:
                    elementname = elm['name']
                    break
    else:
        nimP.error("Element type is an empty string. Please set an element type name or ID")
        return ""

    basepaths = nimApi.get_paths( item=parent, ID=parentID )
    basepath = basepaths['root']
    if elementname in ('plates', 'renders', 'comps'):
       folder =  basepaths[elementname].replace(basepath + '/', '')
    else:
        folder = elementname

    return folder

def buildRenderSceneName( scenepath ):
    """
    Create render scene name from current name
    Name convention:
    [CurrentSceneName]__[timestamp]__RENDER.ext
    """
    (scenename, ext) = os.path.splitext( scenepath )
        # Add timestamp to batch name
    now = datetime.now()
    isonow = now.isoformat()
    timestamp = ''.join( isonow.split('.')[0].split(':') )
    scenename += "__" + timestamp
    # Finish name
    # scenename += "__RENDER.hip" + ".bz2"
    scenename += "__RENDER" + ext
    curdir = os.path.dirname( scenepath )
    # if platform.system() == 'Windows':
        # curdir = curdir.replace( '/', '\\')
    renderscenepath = os.path.join( curdir, scenename)

    # If we decide to put render scenes inside subfolders we can create directories here

    return renderscenepath

def getJobOutputRenderScenePath( renderscene, outputpath, docompress=True ):
    """
    Using  the name from the render scene and its output path constructs the path for the render output scene.
    Optionally add appropiate extension for compression

    Arguments:
        renderscene {str} -- path to render scene
        outputpath {str} -- path to render output path

    Keyword Arguments:
        docompress {bool} -- whether or not compress scene (default: {True})

    Returns:
        str -- path to render scene in job's output dir
    """
    compressed_renderscene = os.path.dirname(outputpath)
    # if platform.system() == 'Windows':
        # compressed_renderscene = compressed_renderscene.replace( '/', '\\' )
    compressed_renderscene = os.path.join( compressed_renderscene, os.path.basename(renderscene))
    if docompress:
        compressed_renderscene += '.bz2'
    return compressed_renderscene


def saveJobOutputRenderScene(  renderscene, outputpath, docompress=True ):
    """
    Save render scene in job output dir.
    By default scene will be compressed

    Arguments:
        renderscene {str} -- path to render scene
        outputpath {str} -- path to render output path

    Keyword Arguments:
        docompress {bool} -- whether or not compress scene (default: {True})
        
    Returns:
        str -- path to saved scene
    """
    import bz2
    import stat
    import shutil

    if not os.path.exists( renderscene):
        raise IOError("Can't save render scene on job output. Source render scene doesn't exist: %s"%renderscene)
    compressed_renderscene = getJobOutputRenderScenePath( renderscene, outputpath, docompress )
    if docompress:
        # Compress render scene
        with open(renderscene, 'rb') as data:
            tarbz2contents = bz2.compress(data.read())

        if not os.path.exists( os.path.dirname( compressed_renderscene ) ):
            try:
                os.makedirs( os.path.dirname(compressed_renderscene) ) 
            except:
                raise
                
        with open(compressed_renderscene, 'wb') as target:
            target.write( tarbz2contents )
    else:
        shutil.copyfle( renderscene, compressed_renderscene )
            
    # Set file read only
    mode = os.stat(compressed_renderscene).st_mode
    ro_mask = 0o777 ^ (stat.S_IWRITE | stat.S_IWGRP | stat.S_IWOTH)
    os.chmod(compressed_renderscene, mode & ro_mask)    

    return compressed_renderscene

def getEXRMetadataAttrsDict(  renderscene, outputpath ):
    '''
    Create a dictionary with attributes for EXR metadata used in our renders

    Arguments:
        renderscene {str} -- Render scene path
        outputpath {str} -- render output path

    Returns:
        dict -- Dictionary with attributes. Key is the attribute name.
    '''
    attrs = {}

    if platform.system() == 'Windows':
        attrs['renderscene'] = re.sub('^\w:', '', renderscene).replace('\\', '/')
        attrs['jobotput_renderscene'] = re.sub('^\w:', '', getJobOutputRenderScenePath( renderscene, outputpath )).replace('\\', '/')
    else:
        attrs['renderscene'] = renderscene
        attrs['jobotput_renderscene'] = getJobOutputRenderScenePath( renderscene, outputpath )
        

    return attrs

def runAsyncCommand( cmd ):
    '''
    Run a command asynchronously.

    Arguments:
        cmd {str} -- command string

    Returns:
        bool -- True if the command finished with errorcode 0, False other wise
    '''
    args = shlex.split(cmd, posix=platform.system() != 'Windows')
    # print(args)
    timeout = 60*2 #some amount of seconds
    delay = 1.0
        
    try:
        proc = Popen(args, shell=True)
    except subprocess.CalledProcessError:
        nimP.errir( "Command: %s "%cmd)
        return False
    except FileNotFoundError:
        nimP.error( "Comand is not available in PATH: %s"%cmd)
        return False
    if sys.version_info >= (3,0):
        # Python 3
        try:
            proc.wait( timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            # outs, errs = proc.communicate()
            nimP.error( "Command timeout: %s "%cmd)
            return False
    else:
        # Python 2
        delay = 1.0
        waittime = int(timeout / delay)
        #while the process is still executing and we haven't timed-out yet
        while proc.poll() is None and waittime > 0:
            #do other things too if necessary e.g. print, check resources, etc.
            time.sleep(delay)
            waittime -= delay
        if waittime < 0:
            proc.kill()
            nimP.error( "Command timeout: %s "%cmd)
            return False
            
    if proc.returncode != 0:
        nimP.error( "Command: %s "%cmd)
        return False

    return True

#
# Publishing
#
def getNextPublishVer ( filename, parent='SHOT', parentID=''):
    '''
    Query NIM's database to get what would be the next version to be publish for the element.

    Arguments
    ---------
        filename : str
            Filename of element to publish. Name convention: [SHOT|ASSET]__[TASK]__[TAG]__[VER].####.ext
        parent : str
            Parent for publish element:SHOT or ASSET
        parentID : str
            Shot or Asset ID

    Returns
    -------
        int 
            Next version for publish or 1 if there is no published file yet
    '''
    # (dirname, filename) = os.path.split(path)
    # Extract basename and ver. Assume name convention is: [SHOT|ASSET]__[TASK]__[TAG]__[VER].####.ext
    basename = filename.split('.')[0]
    basenameparts = basename.split('__')
    basename = '__'.join(basenameparts[:-1]) # Exclude ver part
    curver = basenameparts[-1][1:] # Get ver part and remove the initial v
    # import nuke
    # nuke.tprint("Path: %s"%path)
    # nuke.tprint("Basename: %s, Ver: %s"%(basename, curver))
    if parent == 'SHOT':
        lastver = nimAPI.get_baseVer( shotID=parentID, basename=basename )
    else:
        lastver = nimAPI.get_baseVer( assetID=parentID, basename=basename )
    if lastver:
        # nuke.tprint("Last version available:")
        # nuke.tprint(pformat(lastver, indent=4))
        lastverstr = lastver[0]['version'].encode('utf8')
        newver = int(lastverstr) + 1
        return newver
    else:
        return 1
    pass

def getPublishedVers ( filename, parent='SHOT', parentID='', pub=False):
    '''
    Query NIM's database to get all published version for an element in a shot/asset

    Arguments
    ---------
        filename : str
            Filename of element to query. Name convention: [SHOT|ASSET]__[TASK]__[TAG]__[VER].####.ext
        parent : str
            Parent for publish element:SHOT or ASSET
        parentID : str
            Shot or Asset ID

    Returns
    -------
        int 
            List of versions dictionaries
    '''
    # (dirname, filename) = os.path.split(path)
    # Extract basename and ver. Assume name convention is: [SHOT|ASSET]__[TASK]__[TAG]__[VER].####.ext
    basename = filename.split('.')[0]
    basenameparts = basename.split('__')
    basename = '__'.join(basenameparts[:-1]) # Exclude ver part
    curver = basenameparts[-1][1:] # Get ver part and remove the initial v
    # import nuke
    if parent == 'SHOT':
        vers = nimAPI.get_vers( shotID=parentID, basename=basename )
    else:
        vers = nimAPI.get_vers( assetID=parentID, basename=basename )
    if vers:
        # nuke.tprint("Versions available:")
        # nuke.tprint(pformat(vers, indent=4))
        if pub:
            vers = [ver for ver in  vers if int(ver['isPublished'])==1]
        return vers
    else:
        return False
    pass

def publishOutputPath ( baseloc, shot, name, ver, task,  ext='exr', subtask='', layer='', cat='', subfolder='', isseq=False, format='nim', only_name=False, only_loc=False, force_posix=False  ):
    '''
    Build output path for a publish element
    This is elements name convention:
    - Path
        [JOB]/[work|build]/[SHOT|ASSET]/[ELEMPATH]/[TASK]/[ELEMNAME]__[CAT]/[VER]/
    - Filename:
        [SHOT|ASSET]__[TASK]__[TAG]__[VER].ext

    Supported app output formats
    ----------------------------
    - Houdini (houdini)
    - Nuke (nuke)
    - Nim (nim)

    If we need to store temp files for the render we can use the subfolder option. for instance if we need to store IFD files for Mantra
    we can set subfolder to be 'ifd', extension to be 'ifd', then the file path will be a subfolder in the output location called ifd and the files will have the ifd extension.

    Arguments
    ---------
        baseloc : str
            Base directory for  the files
        shot : str
            Shot/asset name for the render job
        name : str
            Element name
        ver : int
            Element version
        task : str
            Task assigned to render job
        ext : str
            Element file type extension (default: {'exr'})
        subtask : str:
            Extra task definition for more granular setups (default: {''})
        layer : str
            Another extra identifier to group elements, usually by distance or "importance" in the shot.(default: {''})
        cat : str
            Render category, useful to distinguish between final renders and different tests and QD (default: {''})
        subfolder : str
            Used to save temp or auxiliary files for a render. It designates subfolder in the output path to store the files.
        isseq : bool
            Define whether or not the path is a sequence or single file
        format : str
            Output format for host app. this is mostly needed because every app uses a different way of setting padding for sequences.
        only_name : bool
            Just output the file base name without padding or extension. (default: {False})
        only_loc : bool
            Just output the base directory for the output files. (default: {False})
        force_posix : bool
            Force using Posix format even in a Windows environment (default: {False})


    Returns
    -------
        str
            Complete path for the element
    '''
    # nuke.tprint("Output Path Args: BaseLoc: %s, Shot: %s, Name: %s, Ver: %d, Task: %s, Ext: %s, Subtask= %s, Layer=%s, Cat: %s, Subfolder=%s, IsSeq=%d, Format=%s, OnlyName=%d, OnlyLoc=%d, ForcePosix=%d"%\
        # (baseloc, shot, name, ver, task, ext, subtask, layer, cat, subfolder,  isseq, format, only_name, only_loc, force_posix))
    path = ""
    # Task
    if not task:
        # FIXME: do this with log
        print("Task is empty")
    pathtask = task
    if len(subtask) > 0:
        pathtask += "_%s"%subtask

    # Category
    if cat:
        pathcat = 'TEST'
        if cat.upper() == 'AUTO':
            # XXX: the name of the lighting task will probably change
            if task == 'lighting':
                pathcat = 'BTY'
        else:
            pathcat = cat.upper()

    # element Name
    elmname = name
    if len(layer) > 0:
        elmname += "__%s"%layer
    if cat:
        elmname += "__%s"%pathcat

    # Ver
    pathver = "v%03d"%ver

    # Files location
    loc = os.path.normpath( os.path.join(baseloc, pathtask, elmname, pathver))

    # Files Name
    name = "%s__%s__%s__%s"%(shot, pathtask, elmname, pathver)
    if not only_name:
        if isseq:
            if format == 'nim':
                name += ".####.%s"%ext
            elif format == 'houdini':
                name += ".$F4.%s"%ext
            elif format == 'nuke':
                name += ".%"+"04d.%s"%ext
            else:
                name += ".####.%s"%ext # By default use Nim padding format
                
        else:
            name += ".%s"%ext
        
    # Form the final path
    # In Houdini we need to do a expansString weith this output
    path = os.path.join( loc, name )
    if len(subfolder):
        path = os.path.join( loc, subfolder, name )
    if platform.system() == 'Windows' and force_posix:
        path = toPosix( path )
        loc  = toPosix( loc )

    if only_loc:
        return loc
    elif only_name:
        return name
    else:
        return path

def checkFileAndElementPublished( nim ):
    '''
    Check if a file and an element with this basename are already published

    Parameters
    ----------
    nim : NIM Object
        NIM dictionary with all the publish information

    Returns
    -------
    tuple
        Tuple with file and element dictionaries, if any of them is not found the result for that entity will be None
    '''
    file, element = None, None
    basename = nim.name('base')
    ver = nim.version()
    if not basename or not ver:
        P.warning("NIM dictionary doesn't have basename or version information. Basename: %s, Version: %s"%(basename, ver))
        return (file, element)

    if nim.tab() == 'SHOT':
        vers = nimAPI.get_vers( shotID=int(nim.ID('shot')), basename=nim.name('base'))
    else:
        vers = nimAPI.get_vers( assetID=int(nim.ID('asset')), basename=nim.name('base'))
    if vers:
        # pprint(vers)
        for verfile in vers:
            if int(ver) == int(verfile['version']):
                file = verfile
                break
    elmts = nimAPI.get_elements( parent=nim.tab(), parentID=int(nim.ID('shot') if nim.tab() == 'SHOT' else nim.ID('asset')), elementTypeID=int(nim.ID('element')))
    if elmts:
        for elm in elmts:
            if elm['name'] == nim.name('file'):
                element = elm
                break
            
    
    return (file, element)

def pubPath(path, userid, comment="", start=1001, end=1001, handles=0, overwrite=pubOverwritePolicy.NOT_ALLOW, state=pubState.PENDING ,plain=False, jsonout=False, profile=False, dryrun=False, verbose=False):
    '''
    Publish a path pointing to some data in NIM
    The path can point to a single file or a sequence.
    The path needs to be under the project root folder.
    Use pubimport() to move data from an arbitrary location into the project according to the publishing details
    All publishing information will be extracted from the path, so it is suggested to use nim_rohtau.publishOutputPath()
    to correctly construct the path accordding with our name convention

    Overwrite
    ---------
    Overwrite policy is set by the overwrite parameter which can get 3 values:
    - pubOverwritePolicy.NOT_ALLOW : any reuse of a publish item is forbidden. This function will return an error if file version already exists.
    - pubOverwritePolicy.ALLOW_USER: owners can reuse their published items. This function will return an error if an user tries to use file version created by other.
    - pubOverwritePolicy.ALLOW_ALL : All published items can be reused. This function will get the details of the existing items. There won't be redundant publishing

    Parameters
    ----------
    path      : str
        Path to data to publish. I can be a static file or a sequence (User #### for padding)
    userid    : str
        User ID who owns the published item. If not provided use current user
    comment   : str
        Publish comment.
    start     : int
        Start frame.
    end       : int
        End frame.
    handles   : int
        Frame handles.
    overwrite : pub.pubOverwritePolicy
        Overwrite policy. Whether or not allow to reuse pub elements/files
    state     : pub.pubState
        Data state, condition. look pub.pubState. PENDING, AVAILABLE or ERROR.
    plain     : bool
        Output in plain text format.
    jsonout   : bool
        Output in JSON format
    profile   : bool
        Test different stages performance and output results
    dryrun    : bool
        Go thorough the whole process, return information of actions to take but don't modify anything
    verbose   : bool
        Output extra information

    Returns
    -------
    bool
        Dictionary with operation result and published elements IDs. If error then res['success'] is False
    '''
    res = {
        'success'        : False,
        'msg'            : None,
        'filename'       : None,
        'filepath'       : None,
        'version'        : None,
        'fileID'         : None,
        'elementID'      : None,
        'renderID'       : None,
        'extraElementsID': []
    }
    parents = ('SHOW', 'SHOT', 'ASSET')
    taskname = ''
    taskid = 0
    jsonstr = ""

    # Fix path
    posixpath = toPosix( path )
    # Normalize padding format
    posixpath = posixpath.replace('%04d', '####') # Fix Nuke's padding format

    
    nim=Nim.NIM()
    nim.ingest_filePath( filePath=posixpath, checkfile=False )
    if not nim.mode() :
        nim.set_mode('ver')
    # print("NIM Dict:")
    # pprint(nim.get_nim())

    # Get task
    # Try to find a valid task for the task type and user in the shot/asset
    tasks = nimAPI.get_taskInfo( itemClass=nim.tab().lower(), itemID=int(nim.ID('shot')) if nim.tab() == 'SHOT' else int(nim.ID('asset')))
    pubtask = None
    for task in tasks:
        if task['typeID'] == str(nim.ID( elem='task' )) and task['userID'] == nim.ID('user'):
            pubtask = task
            break
    # if pubtask:
        # print("Publish task")
        # pprint(pubtask)

    # First check if there is no file or element published yet with this basename and version
    (file, element) = checkFileAndElementPublished( nim )
    if file:
        res['fileID'] = file['fileID']
    if element:
        res['elementID'] = element['ID']
    if file:
        if overwrite == pubOverwritePolicy.NOT_ALLOW:
            res['success'] = False
            res['msg'] = "File is already published. Overwrite policy disallow re-using published items. Please Up the version: %s v%s"%(nim.name('base'), nim.version())
            if verbose:
                nimP.error("File is already published. Overwrite policy disallow re-using published items. Please Up the version: %s v%s"%(nim.name('base'), nim.version()))
                # pprint(res)
            return res if not plain and not jsonout else False
        elif overwrite == pubOverwritePolicy.ALLOW_USER:
            if int(file['userID']) != userid:
                res['success'] = False
                res['msg'] = "File is already published. Overwrite policy disallow re-using published items not owned by the user. Please Up the version: %s v%s"%(nim.name('base'), nim.version())
                if verbose:
                    nimP.error("File is already published. Overwrite policy disallow re-using published items not owned by the user. Please Up the version: %s v%s"%(nim.name('base'), nim.version()))
                    # pprint(res)
                return res if not plain and not jsonout else False
        else:
            nimP.warning("File is already published. Rendering over previous published item. Consider increment the version: %s v%s"%(nim.name('base'), nim.version()))
                    
    
    # Publish file
    if not file:
        customkeys =  {'Element Type': nim.name('element') if nim.name('element') else 'N/A', 'File Type': nim.nim['fileExt']['fileType'],  'State': pubState.name[state]}
        addfile_result=nimAPI.save_file(parent=nim.tab(), parentID=int(nim.ID('shot') if nim.tab() == 'SHOT' else nim.ID('asset')),\
            task_type_ID=int(nim.ID('task')), userID=userid, basename=nim.name('base'), filename=nim.name('file'), path=nim.filePath(),\
                serverID=int(nim.server('ID')), ext=nim.name('fileExt'), version=int(nim.version()), pub=False, forceLink=False,\
                    customKeys=customkeys)
        if addfile_result['success']:
            res['fileID'] = addfile_result['ID']
        else:
            if verbose:
                nimP.error("Error creating new file publishing %s v%s"%(nim.name('base'), nim.version()))
            res['success'] = False
            res['msg']     = "Error creating new file publishing %s v%s"%(nim.name('base'), nim.version())
            return res if not plain and not jsonout else False

    # Publish element
    # Elements are parent to the same shot/asset of teh file and also "linked" to a task and/or a render preview 
    if not element:
        addelmt_result = nimAPI.add_element( parent=nim.tab().lower(), parentID=int(nim.ID('shot')) if nim.tab() == 'SHOT' else int(nim.ID('asset')), userID=userid, typeID=nim.ID('element'), path=nim.filePath(), name=nim.name('file'), \
            startFrame=start, endFrame=end, handles=handles, metadata='' )
        if not addelmt_result['result']:
            if verbose:
                nimP.error("Error creating new element publishing %s v%s"%(nim.name('base'), nim.version()))
            res['success'] = False
            res['msg']     = "Error creating new element publishing %s v%s"%(nim.name('base'), nim.version())
            # TODO: remove file if it was published correctly
            return res if not plain and not jsonout else False
        else:
            res['elementID'] = addelmt_result['ID']
        if pubtask:
            updateelmt_result = nimAPI.update_element( ID=int(addelmt_result['ID']), taskID=int(pubtask['taskID']))
            if updateelmt_result['success'] != 'true':
                # TODO: remove element and file
                nimAPI.delete_element( res['elementID'] )
                if verbose:
                    nimP.error("Error linking element to task")
                res['success'] = False
                res['msg']     = "Error linking element to task"
                return res if not plain and not jsonout else False
        # TODO: link to render preview if needed

    # Update file
    # Link file to elements and render preview if needed. Update comment
    pubcomment = nim.nim['fileExt']['fileType'] + " %s v%s"%(nim.name('base'), nim.version().zfill(padding)) + ". " + comment.strip("'")
    metadata = {
        'elementID'      : res['elementID'],
        'extraElementsID': res['extraElementsID']
    }
    metadata = json.dumps(metadata)
    updatefile_res = nimAPI.update_file( int(res['fileID']), comment=pubcomment, metadata=metadata )
    if updatefile_res['success'] != 'true':
        if verbose:
            nimP.error("Error updating published file metadata")
        res['success'] = False
        res['msg']     = "Error updating published file metadata"
        return res if not plain and not jsonout else False

    # Update element
    # Link element to file
    metadata = {
        'fileID'      : res['fileID'],
        'extraElementsID': res['extraElementsID']
    }
    metadata = json.dumps(metadata)
    updateelmt_result = nimAPI.update_element( ID=int(res['elementID']), metadata=metadata)
    if updateelmt_result['success'] != 'true':
        nimAPI.delete_element( res['elementID'] )
        if verbose:
            nimP.error("Error updating element metadata")
        res['success'] = False
        res['msg']     = "Error updating element metadata"
        return res if not plain and not jsonout else False

    # Publish successful, finish res dictionary
    res['success']  = True
    res['filename'] = nim.name('file')
    res['filepath'] = nim.filePath()
    res['version']  = nim.version()

    # Grab just published info
    info = nimAPI.get_verInfo( res['fileID'] )
    info = info[0]
    elm = nimAPI.find_elements( name=nim.name('file'), assetID=int(nim.ID('asset')) if nim.tab()=='ASSET' else '', \
        shotID=int(nim.ID('shot')) if nim.tab()=='SHOT' else '')
    elm = elm[0]

    if verbose and not plain and not jsonout and not profile:
        nimP.info("Publishing Details:")
        print("\tName        : %s"%nim.name('file'))
        print("\tVersion     : %s"%nim.version())
        print("\tShot        : %s"%nim.name('shot'))
        print("\tTask        : %s"%nim.name('task'))
        print("\tOwner       : %s"%nim.name('user'))
        print("\tDate        : %s"%info['date'])
        print("\tFile Type   : %s"%nim.nim['fileExt']['fileType'])
        print("\tElement Type: %s"%nim.name('element'))
        print("\tStart       : %s"%elm['startFrame'])
        print("\tEnd         : %s"%elm['endFrame'])
        print("\tComment     : %s"%info['note'])
        print("\tFile ID     : %s"%info['fileID'])
        print("\tElement ID  : %s"%elm['ID'])
        print("\tPath        : %s"%info['filepath'])
        # This only works on Python 3
        # print(
            # f"{'Name:':<15}{nim.name('file')}",
            # f"\n{'Version:':<15}{nim.version()}",
            # f"\n{'Shot:':<15}{nim.name('shot')}",
            # f"\n{'Task:':<15}{nim.name('task')}",
            # f"\n{'Owner:':<15}{nim.name('user')}",
            # f"\n{'Date:':<15}{info['date']}",
            # f"\n{'File Type:':<15}{nim.nim['fileExt']['fileType']}",
            # f"\n{'Element Type:':<15}{nim.name('element')}",
            # f"\n{'Start:':<15}{elm['startFrame']}",
            # f"\n{'End:':<15}{elm['endFrame']}",
            # f"\n{'Comment:':<15}{info['note']}",
            # f"\n{'File ID:':<15}{info['fileID']}",
            # f"\n{'Element ID:':<15}{elm['ID']}",
            # f"\n{'Path:':<15}{info['filepath']}",
        # )
    if  not jsonout and not profile:
        if not file:
            print("New file successfully published!:\nPublish Name: %s,  Version: %s, FileID: %s, ElementID: %s"%(nim.name('file'), nim.version(), info['fileID'], elm['ID']))
        else:
            print("File was already published")
        print("\n")
        

    if jsonout and not profile:
        info = nimAPI.get_verInfo( res['fileID'] )
        info = info[0]
        elm = nimAPI.find_elements( name=nim.name('file'), assetID=int(nim.ID('asset')) if nim.tab()=='ASSET' else '', \
            shotID=int(nim.ID('shot')) if nim.tab()=='SHOT' else '')
        elm = elm[0]
        out = {
            'file'   : info,
            'element': elm
        }
        jsonstr = json.dumps(out, indent=4)
        

    if plain or profile:
        return True
    elif jsonout and not profile:
        return jsonstr
    else:
        return res

    pass

def setPubState(filename="", job= "", parent="", parentID="", state=pubState.PENDING, verbose=False):
    '''
    Set the data state for a published file.
    File is defined by a filename or basename

    Data State
    ----------
    Data  condition is defined in pub.pubState:
        class pubState:
            PENDING   = 0 # Data is being processed, not yet ready. For instance shot is still in render
            AVAILABLE = 1 # Data is ready and available
            ERROR     = 2 # There was an error and data is not healthy
            name      = ('Pending', 'Available', 'Error') # state names
    Usually data starts by default at PENDING, until processign has finished successfully. 
    If processing, rendering, is done correctly then status is changed to AVAILABLE
    If there is any error then it is changed to ERROR

    Filename or Basename
    --------------------
    If the first argument is a filename only that basename and version will be modified.
    On the other hand if a basename is passed all version will be modified.
    Filename convention:  [SHOT|ASSET]__[TASK]__[TAG]__[VER].####.ext
    Basename convention:  [SHOT|ASSET]__[TASK]__[TAG]
    Examples:
        Filename: RND_001__comp__comp__OUT__v007.####.exr
        Basename: RND_001__comp__comp__OUT
    

    Parameters
    filename : str
        Filename of element to query. Name convention: [SHOT|ASSET]__[TASK]__[TAG]__[VER].####.ext
        It can also be in the form of a basename without version information:  [SHOT|ASSET]__[TASK]__[TAG]
    job : str
        number or ID for job
    parent : str
        Parent for publish element:SHOT or ASSET
    parentID : str
        Shot or Asset ID 
    version : int, optional
        Version number if file is designed by basename, by default 1
    state : pub.pubState
        Data state, condition. look pub.pubState. PENDING, AVAILABLE or ERROR.
    verbose : bool
        Output extra information

    Returns
    -------
    bool
        False if an error occurs. Otherwise True
    '''

    ver = 0
    parentname = ""
    jobid, jobnumber = 0, ""

    if job:
        (jobid, jobnumber) = nimUtl.getjobIdNumberTuple( job )
        if not jobid:
            sys.exit()

    if (isinstance(parentID, int) and parentID>0) or (isinstance(parentID, str) and len(parentID) > 0):
        if not isinstance(parentID, int) and not parentID.isnumeric():
            if not jobid:
                log("If parent is defined as a name, a job number or ID need to be provided")
                return False
            parentname = parentID
            if parent.upper() == 'SHOT':
                id = nimUtl.getshotIdFromName( jobid, parentname )
            else:
                id = nimUtl.getassetIdFromName( jobid, parentname )
                
            if not id:
                log("Couldn't find shot/asset %s in %s "%(parentname, jobnumber), severity='error')
                return False
        else:
            id=int(parentID)
            if parent.upper() == 'SHOT':
                parentname = nimAPI.get_shotInfo( shotID=id)[0]['shotName']
            else:
                parentname = nimAPI.get_asseetInfo( shotID=id)[0]['assetName']
    else:
        nimP.error("Need to provide a parent name or ID. It will be a shot name or ID, asset name or ID, etc ...")
        return False

    base= filename.split('.')[0]
    base = base.split('__')
    ver = int(base[-1][1:])
    shotname = base[0]
    base= '__'.join(base[0:-1]) # Remove version

    # Check naming convention, if shot/asset name in basename doesn't match provided parentname then error
    if shotname != parentname:
        nimP.error("Wrong basename name. Basename %s shot/asset and selected shot/assset are different: %s / %s"%(base, shotname, parentname))
        return False

    if parent.upper() == 'SHOT':
        vers = nimAPI.get_vers( shotID=id, basename=base)
    else:
        vers = nimAPI.get_vers( assetID=id, basename=base)
    if vers:
        # pprint(vers)
        if verbose:
            nimP.info("Modify state for publish item %s at %s %s"%(base, parent.lower(), parentname))
        for verfile in vers:
            if filename:
                if int(verfile['version']) != ver:
                    continue
            
            # customkeys =  {'Element Type': nim.name('element') if nim.name('element') else 'N/A', 'File Type': nim.nim['fileExt']['fileType'],  'State': pubState.name[state]}
            customkeys = verfile['customKeys']
            customkeys['State'] = pubState.name[state]
            res = nimAPI.update_file( verfile['fileID'], customKeys=customkeys)
            # pprint(res)
            if res['success'] == 'true':
                nimP.info("Item %s state changed to: %s"%(verfile['filename'], pubState.name[state]))
            else:
                nimP.error("Couldn't change state for %s"%verfile['filename'])
                pprint(res)

    return True



#
# UI
#
class DisplayMessage( QtGui.QDialog ) :

    def __init__(self, msg, title="Display Message", buttons=("Ok",), default_button=0, details="", parent=None) :
        '''
        Inspired in houdini's displayMessage, simple modal dialog to present a message and have the user
        the option to choose Ok by default. An optional button can be added.


        Arguments:
            msg {str} -- Message to show

        Keyword Arguments:
            title {str} -- Window title (default: {""})
            buttons {tuple} -- Labels of buttosn to show (default: {("Ok",)})
            default_button {int} -- Default button index returned if Enter or window is closed (default: {0})
            parent {[type]} -- Parent UI dialog, usually None (default: {None})
        '''
        super( DisplayMessage, self ).__init__(parent)
        self.value          = default_button
        self.msg            = msg
        self.title          = title
        self.labels         = buttons
        self.default_button = default_button
        self.details        = details
        self.buttons        = []
        self.Info           = 0
        self.Warning        = 1
        self.Error          = 2
        
        #  Layouts :
        self.layout=QtGui.QVBoxLayout()
        self.setLayout( self.layout )
        
        #  Text :
        self.textLayout = QtGui.QHBoxLayout()
        self.icon = QtGui.QLabel() 
        # TODO: add severity parameter and change icon accordantly 
        # https://joekuan.files.wordpress.com/2015/09/screen3.png
        self.icon.setPixmap(self.style().standardPixmap(self.style().SP_MessageBoxInformation))
        # self.icon.setPixmap(self.style().standardPixmap(self.style().SP_MessageBoxQuestion))
        # self.icon.setPixmap(self.style().standardPixmap(self.style().SP_MessageBoxWarning))
        # self.icon.setPixmap(self.style().standardPixmap(self.style().SP_MessageBoxCritical))
        self.text=QtGui.QLabel(self.msg)
        self.textLayout.addWidget(self.icon)
        self.textLayout.addWidget(self.text)
        self.layout.addLayout( self.textLayout )
        # Details
        self.detail=QtGui.QTextEdit(self.details)
        if self.details:
            self.detail.setReadOnly( True )
            self.detail.hide()
            self.layout.addWidget( self.detail )
        
        #  Button Layout :
        self.btn_layout=QtGui.QHBoxLayout()
        self.layout.addLayout( self.btn_layout, alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom )
        self.btn_layout.addStretch()

        #  Create Buttons :
        for label, idx in zip(self.labels, list(range(len(self.labels)))):
            button = QtGui.QPushButton( label )
            button.my_own_data = str(idx)  # <<< set your own property
            button.clicked.connect( self.click_handler )
            sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Preferred)
            button.setSizePolicy( sizePolicy )
            self.btn_layout.addWidget( button )
        if self.details:
            button = QtGui.QPushButton( "Show Details ..." )
            button.clicked.connect( self.click_details )
            self.btn_layout.addWidget( button )
            

        # Title
        self.setWindowTitle(title)

        # window.setWindowFlags(window.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)    
        self.setModal( True )
        self.show()
        
        return
    
    def click_handler( self ) :
        'Sets the value to be returned, when a button is pushed'
        target = self.sender()  # <<< get the event target, i.e. the button widget
        data = target.my_own_data  # <<< get your own property
        # nuke.tprint("Pressed button: %d"%int(data))
        self.value = int(data)
        self.close()
        return

    def click_details( self ) :
        'Show details text'
        target = self.sender()  # <<< get the event target, i.e. the button widget
        self.detail.show()
        # data = target.my_own_data  # <<< get your own property
        # nuke.tprint("Pressed button: %d"%int(data))
        # self.value = int(data)
        # self.close()
        return
    
    def btn(self) :
        'Returns the button that was pushed'
        return self.value

    def CloseEvent( self, event):
        nuke.tprint("Closing ....")
    
    @staticmethod
    def get_btn( msg, title="", buttons=("Ok",), default_button=0, details='', parent=None )  :
        'Returns the name of the button that was pushed'
        dialog=DisplayMessage( msg, title=title, buttons=buttons, default_button=default_button, details=details, parent=parent)
        # mainapp = QtGui.QApplication.activeWindow()
        # dialog=DisplayMessage( msg, title=title, buttons=buttons, default_button=default_button, parent=mainapp)
        result=dialog.exec_()
        value=dialog.btn()
        return value

    pass
