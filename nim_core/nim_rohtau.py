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
import shutil
import stat
from glob import glob
from subprocess import Popen
from datetime   import datetime
from pprint     import pprint
from pprint     import pformat
builtin_mod_available = True
try:
    from builtins import range
except:
    # If builtin module is not available this means we are using a python2 without the future package install.
    # This flag will be use to call to regular range() if the builtin version doesn't exists.
    builtin_mod_available = False
# from urllib.parse import uses_relative

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
from .import imgpadding 

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
            # Only print error if we re inside a DCC tool
            # print("NIM: Failed to UI Modules - UI")
            pass


#
# Globals
#

# List of tasks available in publishing system
pubTasksList = ['', 'camera', 'model', 'anim', 'fx', 'light', 'comp', 'layout', 'lookdev', 'cfx', 'rig', 'pack', 'track', 'conform']
# List of elements available in publishing system
pubElementsList = ['', 'plates', 'comps', 'renders', 'cache', 'camera', 'prep', 'precomp', 'roto', 'dmp']
# User mask. Only user can write/delete
user_mask = 0o777 ^ (stat.S_IWGRP | stat.S_IWOTH)
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

class reviewType:
    '''
    Enum for different item types
    '''
    NOTYPE        = 0 # Disable review type
    DAILY         = 1 # Review for dailies
    EDIT          = 2 # Review for Editorial
    REF           = 3 # Review used for referrencies
    MAKEOF        = 4 # Used for making offs
    name          = ('N/A', 'Daily', 'Edit', 'Reference', 'Making Of') # types names

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

def elementTypeFolder( elementtype, parent, parentID, outFullPath=False ):
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
    elementname=""
    folder = ""
    if len(elementtype) > 0:
        elmtsTypes = nimAPI.get_elementTypes()
        # pprint(elmtsTypes)
        if not elementtype.isnumeric():
            elementname = elementtype
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

    basepaths = nimAPI.get_paths( item=parent, ID=parentID )
    basepath = basepaths['root']
    if elementname in ('plates', 'renders', 'comps'):
       folder =  basepaths[elementname].replace(basepath + '/', '')
    else:
        # Put non special elements under the pub folder
        # folder = "pub/%s"%elementname
        folder = elementname

    return folder

def validateFilename( name ):
    '''
    Check if a file name is correct for us to process.
    Also check if the filename represents as file sequence

    Valid Name
    ----------
    A valid name will be imn the form:
        FileName.Frames.Ext
    Frames wil have a maximum padding of nim_core.imgpadding. At  the moment is 4.
    If padding exists then it will be assumed to be a sequence.
    Filename, frames and ext must be separated by the dot sign .

    Parameters
    ----------
    name : str
        Filename string, including name and extension. Path will be removed

    Returns
    -------
    tuple
        Tuple with two boolean elements: isvalid and isseq
    '''
    isvalid = True
    isseq = False
    filename = os.path.basename( name )
    parts = filename.split('.')
    l = len(parts)
    if l < 2 or l > 3:
        nimP.error("Filename not in accordance with convention, needs to have at least name and  extension with optional frames padding: %s"%filename)
        isvalid = False
    isseq = l == 3
    if isseq:
        if not len(parts[1]) or  len(parts[1]) > imgpadding:
            nimP.error("Wrong frame padding, the maximum length id %d"%imgpadding)
            isvalid = False
            
    return (isvalid, isseq)

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
    Optionally add appropriate extension for compression

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
    # If scene already exists then just return
    if os.path.exists(compressed_renderscene):
        return compressed_renderscene
    if docompress:
        if not os.path.exists( os.path.dirname( compressed_renderscene ) ):
            try:
                os.makedirs( os.path.dirname(compressed_renderscene) ) 
            except:
                raise
        # Compress render scene
        with open(renderscene, 'rb') as data:
            tarbz2contents = bz2.compress(data.read())
                
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
        nimP.error( "Command: %s "%cmd)
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

def createDraftMovie( infile, frames, outfile='', drafttemplate='', overrideres='', overrideoutcolor='', verbose=False):
    '''
    Create a movie for review from a image sequence using Deadline's Draft
    
    If outfile is not provided it will create the movie in a subfolder in the location of the image sequence called Draft.
    The name of the movie will be the same as the image sequence.
    If outfile is a folder it will create a movie using the same name as the input sequence under the indicated folder.

    Draft Template
    --------------
    The default Draft template is:
        /studio/pipeline/deadline/draft/standaloneDraftCreateSimpleMovie.py
    It can be override using the envar RT_DRAFT_TEMPLATE
    Or with the drafttemplate argument

    Parameters
    ----------
    infile : str
        Path to image sequence in the form: /pathtoseq/seqname.####.exr
    frames : str
        String with frame list: start-end. For instance: 1001-1100 or 1001
    outfile : str, optional
        If provided output folder or file for draft movie, by default ''
    drafttemplate : str, optional
        Alternative Draft template instead of studio default, by default ''
    overrideres : str, optional
        Override draft template resolution, by default ''. Example: 1920x1280
    overrideoutcolor : str, optional
        Override OCIO color role, by default ''. For example: color_picking
    verbose : bool, optional
        Output extra information, by default False

    Returns
    -------
    str
        Path to draft movie or False if error.
    '''
    # set PYTHONPATH=c:\dev\deadlinerepository10\draft\Windows\64bit
    # set MAGICK_CONFIGURE_PATH=c:\dev\deadlinerepository10\draft\Windows\64bit 
    #  \opt\deadline10\bin\dpython \studio\pipeline\deadline\draft\DraftCreateSimpleMovie.py frameList start-end inFile renderedframespath outFile renderoutput/Draft/draft.mov

    # XXX: careful here these paths to dpython are harcoded. This will be a
    # problem someday ...
    # Use Deadline's python
    cmd = "/opt/Thinkbox/Deadline10/bin/dpython" # For unix like systems
    if platform.system() == 'Windows':
        cmd = "C:\\opt\\deadline10\\bin\\dpython"
    # Default studio Draft template, or use override from envvar or override from argument.
    draftTemplate="/studio/pipeline/deadline/draft/standaloneDraftCreateSimpleMovie.py"
    if 'RT_DRAFT_TEMPLATE' in os.environ:
        draftTemplate = os.getenv('RT_DRAFT_TEMPLATE')
    if drafttemplate:
        draftTemplate = drafttemplate
    cmd += " %s "%os.path.normpath(draftTemplate)
    # Frames list
    if not frames.count('-'):
        start = frames
        end = start
    else:
        framesrange = frames.split('-')
        start = framesrange[0]
        end = framesrange[1]
    if not start.isdigit() or not end.isdigit():
        nimP.error("Wrong frames range string, start and/or end are not numbers: %s"%frames)
        return False
    cmd += " frameList=%s-%s"%(start, end)
    # In Seq
    path     = infile
    path     = path.replace('%04d', '####') # Fix Nuke's padding format
    path     = path.replace('$F5', '#####') # Fix Houdini's padding format
    path     = path.replace('$F4', '####') # Fix Houdini's padding format
    path     = path.replace('$F', '#') # Fix Houdini's padding format
    path     = os.path.normpath(path)
    if platform.system() == 'Windows':
        path = os.path.join('C:', path)
    cmd += " inFile=%s "%path
    # Out draft movie path
    outdraft = os.path.join( os.path.dirname(path), 'Draft' ) # Draft location
    (basename, tagname, ver) = nimAPI.extract_basename( filepath=os.path.basename(path) )
    draftname = "%s_v%s.mov"%(basename, str(ver).zfill(2))
    # draftname = os.path.basename(path).split('.')[0] + ".mov" # Draft name
    if outfile:
        if len(os.path.splitext(outfile)) >= 2:
            # This is a complete path with filename
            outdraft = os.path.dirname(outfile)
            draftname = os.path.basename(outfile)
        else:
            # We have a folder
            outdraft = outfile
    if not os.path.exists( outdraft ):
        try:
            os.makedirs( outdraft ) 
        except:
            raise
    outdraft = os.path.join(outdraft, draftname)
    cmd += " outFile=%s "%outdraft
    if 'THINKBOX_LICENSE_FILE' not in os.environ:
        nimP.warning("THINKBOX_LICENSE_FILE not present in environment. Initializing to: 27008@lic-server.rohtau.com")
        thinkboclivenv = {'THINKBOX_LICENSE_FILE' : '27008@lic-server.rohtau.com'}
        os.environ.update(thinkboclivenv)
    if not runAsyncCommand( cmd ):
        nimP.error("Can't create Draft review movie: %s"%outdraft)
    
    return outdraft

#
# Publishing
#
def buildBasename( shot, task, name, elemtype='', layer='', isfolder=False):
    '''
    Create basename according to name convention.
    Basename is the portion of the filename without the version string:
        [SHOT|ASSET]__[TASK[_ELEMTYPE]]__[TAG[_LAYER]]

    If isfolder is set then return the folder basename, this is the same as the file basenames except for the shot and tasks names
    which are removed to avoid complexity in the file path. Shot and task are supposed to be already in the path.

    Parameters
    ----------
    shot : str
        Shot/asset name for the render job
    name : str
        Element name
    task : str
        Task assigned to render job
    elemtype : str
        Name of the element being published, like: cg, 2d, cache, cam, etc ... .Not used for scene files. (default: {''})
    layer : str
        Another extra identifier to group elements, usually by distance or "importance" in the shot.(default: {''})
    isfolder : bool
        whether or not return the folder basename. This is the same as the file basename without the shot and task components

    Returns
    -------
    str
        Basename according to name convention
    '''
    if elemtype:
        taskname = "%s_%s"%(task, elemtype)
    else:
        taskname =  task
    # subtask is DEPRECATED
    # if len(subtask) > 0:
        # pathtask += "_%s"%subtask

    # Category
    # DEPRECATED
    '''
    if cat:
        pathcat = 'TEST'
        if cat.upper() == 'AUTO':
            if task == 'light':
                pathcat = 'BTY'
        else:
            pathcat = cat.upper()
    '''

    # element Name
    tag = name
    tag = tag.replace('/', '_') # Fix potential assets names that includes / to separate asset category from name
    if len(layer) > 0:
        tag += "_%s"%layer
    # cat is  DEPRECATED
    # if cat:
        # elmname += "__%s"%cat

    basename = "%s__%s__%s"%(shot, taskname, tag)
    if not tag:
        # No tag
        basename = "%s__%s"%(shot, taskname)

    if isfolder:
        return tag
    else:
        return basename

def getNextPublishVer ( filename, parent='SHOT', parentID=''):
    '''
    Query NIM's database to get what would be the next version to be publish for the element.

    Filename or Basename
    --------------------
    Filename:
        [SHOT|ASSET]__[[ELEMTYPE_]TASK]__[TAG]__[VER].####.ext
    Basename:
        [SHOT|ASSET]__[[ELEMTYPE_]TASK]__[TAG]
    
    

    Arguments
    ---------
        filename : str
            Filename or basename of element to publish.
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
    # (basename, shotname, tasktype, elem, tag, ver) = nimUtl.splitName(filename)
    fileparts = nimUtl.splitName(filename)
    '''
    if filename.count('.')>0:
        basename = filename.split('.')[0]
    else:
        basename = filename
    basenameparts = basename.split('__')
    if basenameparts[-1].startswith('v') or basenameparts[-1].startswith('V'):
        basename = '__'.join(basenameparts[:-1]) # Exclude ver part
    curver = basenameparts[-1][1:] # Get ver part and remove the initial v|V
    '''
    if parent == 'SHOT':
        lastver = nimAPI.get_baseVer( shotID=parentID, basename=fileparts['base'] )
    else:
        lastver = nimAPI.get_baseVer( assetID=parentID, basename=fileparts['base'] )
    if lastver:
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
    if parent == 'SHOT':
        vers = nimAPI.get_vers( shotID=parentID, basename=basename )
    else:
        vers = nimAPI.get_vers( assetID=parentID, basename=basename )
    if vers:
        if pub:
            vers = [ver for ver in  vers if int(ver['isPublished'])==1]
        return vers
    else:
        return False
    pass

def publishOutputPath ( baseloc, shot, name, ver, task, elem='', ext='exr', layer='', subfolder='', isseq=False, format='nim', only_name=False, only_loc=False, force_posix=False  ):
    '''
    Build output path for a publish element according with the name convention
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

    If we need to store temp files for the render we can use the subfolder option. For instance if we need to store IFD files for Mantra
    we can set subfolder to be 'ifd', extension to be 'ifd', then the file path will be a subfolder in the output location called ifd and the files will have the ifd extension.

    Arguments
    ---------
        baseloc : str
            Base directory fore the files
        shot : str
            Shot/asset name for the render job
        name : str
            Element name
        ver : int
            Element version
        task : str
            Task assigned to render job
        elem : str:
            Element type name
        ext : str
            Element file type extension (default: {'exr'})
        layer : str
            Another extra identifier to group elements, usually by distance or "importance" in the shot.(default: {''})
        subfolder : str
            Used to save temp or auxiliary files for a render. It designates subfolder in the output path to store the files.
        isseq : bool
            Define whether or not the path is a sequence or single file
        format : str
            Output format for host app. This is mostly needed because every app uses a different way of setting padding for sequences.
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
        nimP.warning("Can't get a correct path for publishing, task is empty")
    pathtask = task
    # subtask is DEPRECATED
    # if len(subtask) > 0:
        # pathtask += "_%s"%subtask

    # Category is DEPRECATED
    # Category
    '''
    if cat:
        pathcat = 'TEST'
        if cat.upper() == 'AUTO':
            if task == 'light':
                pathcat = 'BTY'
        else:
            pathcat = cat.upper()
    '''

    # Ver
    pathver = "v%s"%str(ver).zfill(padding)

    # Files location
    basename = buildBasename( shot, task, name, elemtype=elem, layer=layer)
    loc = os.path.normpath( os.path.join(baseloc, pathtask, basename, pathver))
    # folderbasename = buildBasename( shot, task, name, subtask=subtask, layer=layer, cat=cat, isfolder=True)
    # loc = os.path.normpath( os.path.join(baseloc, pathtask, folderbasename, pathver))

    # Files Name
    filename = "%s__%s"%(basename, pathver)
    if not only_name:
        if isseq:
            if format == 'nim':
                filename += ".####.%s"%ext
            elif format == 'houdini':
                filename += ".$F4.%s"%ext
            elif format == 'nuke':
                filename += ".%"+"04d.%s"%ext
            else:
                filename += ".####.%s"%ext # By default use Nim padding format
                
        else:
            filename += ".%s"%ext
        
    # Form the final path
    # In Houdini we need to do a expansString weith this output
    path = os.path.join( loc, filename )
    if len(subfolder):
        path = os.path.join( loc, subfolder, filename )
    if platform.system() == 'Windows' and force_posix:
        path = toPosix( path )
        loc  = toPosix( loc )

    if only_loc:
        return loc
    elif only_name:
        return basename
    else:
        return path

def checkFileAlreadyPublished( nim ):
    '''
    Check if a file is already published and with a different File Type in custom keys.
    This allows to check if we are trying to publish to different file types with the same
    name.
    For instance publish a scene with the same name for Houdini and Nuke, or publishing a 
    render with the same name as the scene.

    Parameters
    ----------
    nim : NIM Object
        NIM dictionary with all the publish information

    Returns
    -------
    dict
        Dict with two keys: success and type. If error return dict with success key set as False and type with the file type of the existing publish.
    '''
    res = {'success' : True}
    mycustomkeys =  {'Element Type': nim.name('element') if nim.name('element') else 'N/A', 'File Type': nim.nim['fileExt']['fileType']}
    basename = nim.name('base')
    ver = nim.version()
    if not basename or not ver:
        nimP.warning("NIM dictionary doesn't have basename or version information. Basename: %s, Version: %s"%(basename, ver))
        res['success'] = True
        return res

    if nim.tab() == 'SHOT':
        vers = nimAPI.get_vers( shotID=int(nim.ID('shot')), basename=nim.name('base'))
    else:
        vers = nimAPI.get_vers( assetID=int(nim.ID('asset')), basename=nim.name('base'))
    if vers:
        fileinfo = vers[0]
        customkeys = fileinfo['customKeys']
        if 'File Type' in customkeys and customkeys['File Type'] != mycustomkeys['File Type']:
            res['success'] = False
            res['type'] = customkeys['File Type']
            return res

    return res

def checkFileAndElementPublished( nim ):
    '''
    Check if a file and an element with this basename is already published

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
        nimP.warning("NIM dictionary doesn't have basename or version information. Basename: %s, Version: %s"%(basename, ver))
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

def createRenderIcon( elementInfo ):
    '''
    Using the dictionary with information about an element, get middle frame and generate an icon for a render publish

    Parameters
    ----------
    elementInfo : dict
        Published element dictionary. Don't confuse with the File, here we need to pass the element for the render

    Returns
    -------
    str
        Path to icon or False if error
    '''
    import tempfile

    middleframe = int(( int(elementInfo['endFrame']) - int(elementInfo['startFrame'])) / 2)
    middleframe = int(elementInfo['startFrame']) + middleframe
    middleframe = str(middleframe).zfill(imgpadding)
    middlepath = elementInfo['path'].replace('####', middleframe)
    middlepath = os.path.normpath(middlepath)
    if platform.system() == 'Windows':
        middlepath = os.path.join('C:', middlepath)
    if not os.path.exists(middlepath):
        nimP.error("Frame for render icon doesn't exists: %s"%middlepath)
        return False
    filename = os.path.basename(middlepath)
    rendername = filename.split('.')[0]
    iconname = rendername + ".jpg"
    iconpath = os.path.join(tempfile.gettempdir(), iconname)
    print("Create icon from: %s"%middlepath)
    print("Crete icon at: %s"%iconpath)

    # XXX: careful here these paths to dpython are harcoded. This will be a
    # problem someday ...
    cmd = "/opt/Thinkbox/Deadline10/bin/dpython" # For unix like systems
    if platform.system() == 'Windows':
        cmd = "C:\\opt\\deadline10\\bin\\dpython"
    # Default studio Draft template, or use override from envvar or override from argument.
    draftTemplate="/studio/pipeline/deadline/draft/standaloneDraftCreateRenderIcon.py"
    cmd += " %s "%os.path.normpath(draftTemplate)
    # In Frame
    cmd += " inFile=%s "%middlepath
    # Out render icon path
    cmd += " outFile=%s "%iconpath
    if 'THINKBOX_LICENSE_FILE' not in os.environ:
        nimP.warning("THINKBOX_LICENSE_FILE not present in environment. Initializing to: 27008@lic-server.rohtau.com")
        thinkboclivenv = {'THINKBOX_LICENSE_FILE' : '27008@lic-server.rohtau.com'}
        os.environ.update(thinkboclivenv)
    try:
        ret = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        nimP.error("Draft command for render icon generation: %s "%cmd)
        nimP.error("Command: %s"%e.cmd)
        nimP.error("Outut: %s"%e.output)
        nimP.error("Error code: %d"%e.returncode)
        return False
    except FileNotFoundError:
        nimP.error( "Can't find command in path %s"%cmd.split()[0])
        return False
    print("Output:")
    print(ret)
    # if not runAsyncCommand( cmd ):
        # nimP.error("Can't create Render Icon: %s"%iconpath)
    
    return iconpath

def pubPath(path, userid, comment="", start=1001, end=1001, handles=0, overwrite=pubOverwritePolicy.NOT_ALLOW, state=pubState.PENDING , plain=False, jsonout=False, profile=False, dryrun=False, verbose=False):
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

    Publish Render
    --------------
    Publish file as a render element. Render ID is returned in the output dir for further adding icons and review elements.

    Parameters
    ----------
    path      : str
        Path to data to publish. I can be a static file or a sequence (User #### for padding)
    userid    : int
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
    posixpath = posixpath.replace('$F5', '#####') # Fix Houdini's padding format
    posixpath = posixpath.replace('$F4', '####') # Fix Houdini's padding format
    posixpath = posixpath.replace('$F', '#') # Fix Houdini's padding format

    
    nim=Nim.NIM()
    nim.ingest_filePath( filePath=posixpath, checkfile=False )
    if not nim.mode() :
        nim.set_mode('ver')

    # print("NIM Dict:")
    # pprint(nim.get_nim())
    # import nuke
    # nuke.tprint("NIM Dict:")
    # nuke.tprint(pformat(nim.get_nim()))

    # userid
    if not userid:
        myuser = nimAPI.get_user()
        userid = int(nimAPI.get_userID(myuser))

    # Get task
    # Try to find a valid task for the task type and user in the shot/asset
    if not nim.ID( elem='task' ):
        res['msg'] = "couldn't find a supported task in the path: %s"%path
    pid = nim.ID('shot') if nim.tab() == 'SHOT' else nim.ID('asset')
    if not pid:
        res['msg'] = "Shot or Asset name in path doesn't exists"
        return res
    else:
        pid = int(pid)
    pubtask = nimUtl.getuserTask( userid, tasktype=int(nim.ID( elem='task' )), parent=nim.tab().lower(), parentID=pid) 
    '''
    tasks = nimAPI.get_taskInfo( itemClass=nim.tab().lower(), itemID=int(nim.ID('shot')) if nim.tab() == 'SHOT' else int(nim.ID('asset')))
    pubtask = None
    for task in tasks:
        if task['typeID'] == str(nim.ID( elem='task' )) and task['userID'] == nim.ID('user'):
            pubtask = task
            break
    # if pubtask:
        # print("Publish task")
        # pprint(pubtask)
    '''

    # Check if there is already a file published with different file type
    check_res = checkFileAlreadyPublished( nim )
    if not check_res or not check_res['success']:
        res['success'] = False
        res['msg'] = "A file with name %s and file type %s is already published. Trying to save with file type %s. Please change the name of your file."%(nim.name('base'), check_res['type'], nim.nim['fileExt']['fileType'])
        nimP.error(res['msg'])
        return res if not plain and not jsonout else False

    # Check if there is no file or element published yet with this basename and version
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
        addfile_result=nimAPI.save_file(parent=nim.tab(), parentID=pid, task_type_ID=int(nim.ID('task')), userID=userid, basename=nim.name('base'), \
            filename=nim.name('file'), path=nim.filePath(), serverID=int(nim.server('ID')), ext=nim.name('fileExt'), version=int(nim.version()), \
                pub=False, forceLink=False, customKeys=customkeys)
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
        addelmt_result = nimAPI.add_element( parent=nim.tab().lower(), parentID=pid, userID=userid, typeID=nim.ID('element'), path=nim.filePath(), name=nim.name('file'), \
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

    # Update file
    # Link file to elements and render preview if needed. Update comment
    pubcomment = nim.nim['fileExt']['fileType'] + " %s v%s"%(nim.name('base'), nim.version().zfill(padding)) 
    if comment.strip("''"):
        pubcomment += ". " + comment.strip("'")
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
    metampdata = json.dumps(metadata)
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
        res['version']   = int(res['version'])
        res['fileID']    = int(res['fileID'].encode('ascii'))
        res['elementID'] = int(res['elementID'].encode('ascii'))
        return res

    pass

def setPubState(fileID= None, filename="", job= "", parent="", parentID="", state=pubState.PENDING, verbose=False, nimURL=None, apiKey=None ):
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

    If parentID, name or ID of shot or asset is not provided it will be extracted from the file name itself.

    If fileID is supplied then filename, job, parent and/or parentID are not needed, File to be modified will be refered directly from it's ID.
    This is the most straightforward way of using this function.
    

    Parameters
    ----------
    fileID : int
        File ID. If this is supplied then filename, job, parent and parent ID are not needed.
    filename : str
        Filename of element to query. Name convention: [SHOT|ASSET]__[TASK]__[TAG]__[VER].####.ext
        It can also be in the form of a basename without version information:  [SHOT|ASSET]__[TASK]__[TAG]
    job : str
        number or ID for job
    parent : str
        Parent for publish element:SHOT or ASSET
    parentID : int
        Shot or Asset ID 
    version : int, optional
        Version number if file is designed by basename, by default 1
    state : pub.pubState
        Data state, condition. look pub.pubState. PENDING, AVAILABLE or ERROR.
    verbose : bool
        Output extra information
    nimUrl: str
        NIM API Url in case this function is called from a non user environment, for instance the render farm
    apiKey: str
        NIM API key in case this function is called from a non user environment, for instance the render farm

    Returns
    -------
    bool
        False if an error occurs. Otherwise True
    '''

    ver = 0
    parentname = ""
    id = 0
    jobid, jobnumber = 0, ""
    fileinfo = None

    if not fileID:
        if job:
            (jobid, jobnumber) = nimUtl.getjobIdNumberTuple( job )
            if not jobid:
                sys.exit()

        # (base, shotname, task, elem, tag, ver) = nimUtl.splitName( filename )
        fileparts = nimUtl.splitName( filename )
        if not fileparts:
            return False
        if not parentID:
            # Get shot or asset name from filename
            parentID = fileparts['shot']

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
                parentname = nimAPI.get_assetInfo( shotID=id)[0]['assetName']


        # Check naming convention, if shot/asset name in basename doesn't match provided parentname then error
        if fileparts['shot'] != parentname:
            nimP.error("Wrong basename name. Basename %s shot/asset and selected shot/assset are different: %s / %s"%(fileparts['base'], fileparts['shot'], parentname))
            return False

        if parent.upper() == 'SHOT':
            vers = nimAPI.get_vers( shotID=id, basename=fileparts['base'])
        else:
            vers = nimAPI.get_vers( assetID=id, basename=fileparts['base'])
        if vers:
            # pprint(vers)
            if verbose:
                nimP.info("Modify state for publish item %s at %s %s"%(fileparts['base'], parent.lower(), parentname))
            for verfile in vers:
                if filename:
                    if int(verfile['version']) != fileparts['ver']:
                        continue
                    else:
                        fileinfo = verfile
                        break
    else:
        # Grab just published info
        info = nimAPI.get_verInfo( fileID )
        fileinfo = info[0]

            
    if fileinfo:
        # customkeys =  {'Element Type': nim.name('element') if nim.name('element') else 'N/A', 'File Type': nim.nim['fileExt']['fileType'],  'State': pubState.name[state]}
        customkeys = fileinfo['customKeys']
        customkeys['State'] = pubState.name[state]
        res = nimAPI.update_file( fileinfo['fileID'], customKeys=customkeys)
        # pprint(res)
        if res['success'] == 'true':
            nimP.info("Item %s state changed to: %s"%(fileinfo['filename'], pubState.name[state]))
        else:
            nimP.error("Couldn't change state for %s"%fileinfo['filename'])
            pprint(res)

    return True

def pubRender(fileID='', filename='', job='', userid ='', parent="shot", parentID="", renderkey='', comment='', rendertype='', starttimedate='', endtimedate='', icon='', verbose=False):
    '''
    Publish a new render from a basename
    This is needed to get file sequences available in the render and review sections

    Filename or Basename
    --------------------
    The first argument is a filename only that basename and version will be modified.
    Filename convention:  [SHOT|ASSET]__[TASK[_ELEMTYPE]]__[TAG]__[VER].####.ext
    Examples:
        Filename: RND_001__comp_2d__OUT__v007.####.exr

    Time
    ----
    starttimedate and endtimedate are expected to be passed in datetime.isoformat: 2015-02-04T20:55:08.914461+00:00
    NIM uses this date time format: "2017-01-01 08:00:00"

    Render Key
    ----------
    When publishing from the farm we need a way to link several publishing stages to the same render.
    This is done using the farm job id as part of the log for the render in NIM.
    This allows to refer to a rent item in NIM without knowing the render ID.
    With this method the publishing process can be splitted into different stages, like one task publishing the render and another
    in parallel creating the Draft review movie.
    

    Parameters
    ----------
    filename : str
        Filename of element to query. Name convention: [SHOT|ASSET]__[TASK[_ELEMTYPE]]__[TAG]__[VER].####.ext
    userid    : int
        User ID who owns the published item.
    job : str
        number or ID for job
    parent : str
        Parent for publish element:SHOT or ASSET
    parentID : str
        Shot or Asset ID
    renderkey : str
        Render ID in the farm. For instance from Deadline wit will be Deadline's job id.
    comment   : str
        Render comment.
    rendertype   : str
        Render source, Nuke, Mantra, Vray, etc ....
    frames   : str
        Frames list: 1001-1100
    starttimedate   : str
        Render start in UTC
    endtimedate      : str
        Render end in UTC
    icon : str
        Path to an image to be used as icon for the renders
    verbose : bool
        Output extra information

    Returns
    -------
    dict
        Dictionary with keys:
        - success: bool
        - msg: string with error message
        - ID: string with renderID number
    '''
    ver = 0
    parentname = ""
    jobid, jobnumber = 0, ""
    res = {'success' : False}
    fileInfo = None


    if not fileID:
        if not filename:
            if verbose:
                nimP.error("Need to provide a FileID or a filename in order to publish a render from them")
            res['success'] = False
            res['msg']     = "Need to provide a FileID or a filename in order to publish a render from them"
            return res
            return False
        
        if not userid or not nimUtl.getuserName(userid):
            nimP.error("Wrong user id: %d"%userid)
            
        # (base, shotname, task, tag, ver) = nimUtl.splitName( filename )
        fileparts = nimUtl.splitName( filename )
        if not parentID:
            # Use shot/asset name from file name if not provided
            parentID = fileparts['shot']

        if (isinstance(parentID, int) and parentID>0) or (isinstance(parentID, str) and len(parentID) > 0):
            if not isinstance(parentID, int) and not parentID.isnumeric():
                if job:
                    (jobid, jobnumber) = nimUtl.getjobIdNumberTuple( job )
                    if not jobid:
                        sys.exit()
                elif not job or not jobid:
                    if verbose:
                        nimP.error("If parent is defined as a name, a job number or ID need to be provided")
                    res['success'] = False
                    res['msg']     = "If parent is defined as a name, a job number or ID need to be provided"
                    return res
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
                    parentname = nimAPI.get_assetInfo( shotID=id)[0]['assetName']
        else:
            if verbose:
                nimP.error("Need to provide a parent name or ID. It will be a shot name or ID, asset name or ID, etc ...")
            res['success'] = False
            res['msg']     = "Need to provide a parent name or ID. It will be a shot name or ID, asset name or ID, etc ..."
            return res


        # Check naming convention, if shot/asset name in basename doesn't match provided parentname then error
        if fileparts['shot'] != parentname:
            if verbose:
                nimP.error("Wrong basename name. Basename %s shot/asset and selected shot/assset are different: %s / %s"%(fileparts['base'], fileparts['shot'], parentname))
            res['success'] = False
            res['msg']     = "Wrong basename name. Basename %s shot/asset and selected shot/assset are different: %s / %s"%(fileparts['base'], fileparts['shot'], parentname)
            return res

        if parent.upper() == 'SHOT':
            vers = nimAPI.get_vers( shotID=id, basename=fileparts['base'])
        else:
            vers = nimAPI.get_vers( assetID=id, basename=fileparts['base'])
        if vers:
            # pprint(vers)
            for verfile in vers:
                if int(verfile['version']) == fileparts['ver']:
                    fileInfo = verfile
                    break
    else:
        # Grab just published info
        info = nimAPI.get_verInfo( fileID )
        fileInfo = info[0]


    # print("File version to publish render to:")
    # pprint(fileInfo)
    path = fileInfo['filepath']
    # (base, shotname, task, tag, ver) = nimUtl.splitName( fileInfo['filename'] )
    fileparts = nimUtl.splitName( fileInfo['filename'] )
    rendername = fileparts['base'] + "__" + "v%s"%str(fileparts['ver']).zfill(padding)
    id = int(fileInfo['parentID'])
    parent = fileInfo['fileClass'].lower()
    outdir = os.path.dirname(path)
    tasktype = int(fileInfo['task_type_ID'])
    elementInfo = nimAPI.find_elements( name=fileInfo['filename'], assetID=id if parent.upper()=='ASSET' else '', shotID=id if parent.upper()=='SHOT' else '')
    if elementInfo:
        elementInfo=elementInfo[0]
    else:
        nimP.warning("Couldn't find an element for the render")
    # print("Element")
    # pprint(elementInfo)
    task = nimUtl.getuserTask( userid, tasktype=tasktype, parent=parent, parentID=id) 
    if not task:
        user = nimUtl.getuserName(userid)
        if verbose:
            if user:
                msg = "Can't find a task of type %s at %s %s for user %s"%(tasktype, parent.lower(), parentname, user )
            else:
                msg = "Can't find a task of type %s at %s %s for user ID %d"%(tasktype, parent.lower(), parentname, userid )
            nimP.error(msg)
            res['msg']     = msg
            res['success'] = False
            return res
    # print("Task:")
    # pprint(task)
    metadata = eval(fileInfo['metadata'])
    elementID = metadata['elementID'] if 'elementID' in metadata else 0
    elementTypeID = fileInfo['customKeys']['Element Type'] if 'Element Type' in fileInfo['customKeys'] else 0
    rendertimestr = ""
    avgtimestr = ""
    nframes = 0
    if elementInfo:
        nframes = int(elementInfo['endFrame']) - int(elementInfo['startFrame'])

    # Ensure starttimedate and endtimedate are in the correct format.
    # Convert several ISO variants datetime string used by NIM
    # NIM uses this date time format: "2017-01-01 08:00:00" ->
    # "%Y-%m-%d %H:%M:%S"
    # Supported ISO variants: 
    # 2011-11-04
    # 2011-11-04T00:05:23
    # 2011-11-04 00:05:23.283
    # 2011-11-04 00:05:23.283+00:00
    # 2011-11-04T00:05:23+04:00
    # Microseconds are  always removed
    if starttimedate:
        if sys.version_info >= (3,0): # Python 3 returns
            try:
                # Test ISO format
                starttimedate = datetime.fromisoformat(starttimedate)
                starttime = starttimedate.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                nimP.warning("Start date/time format not supported, please use ISO format: 2011-11-04 00:05:23")
                starttimedate = ''
        else:
            # Python 2
            # Supported formats:
            # 2011-11-04 00:05:23 -> Used by NIM
            # 2011-11-04T00:05:23
            if starttimedate.count('.') > 0:
                starttimedate = starttimedate.split('.')[0] # Remove miliseconds. After .
            try:
                #Test ISO format
                starttimedate = datetime.strptime(starttimedate, "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                try :
                    #Test ISO format 2
                    starttimedate = datetime.strptime(starttimedate, "%Y-%m-%dT%H:%M:%S")
                    starttimedate = datetime.strptime(str(starttimedate).replace("T", " "), "%Y-%m-%d %H:%M:%S")
                except ValueError as e:
                    nimP.warning("Start date/time format not supported, please use ISO format: 2011-11-04 00:05:23")
                    starttimedate = ''
            if starttimedate:
                starttime = starttimedate.strftime("%Y-%m-%d %H:%M:%S")


    if endtimedate:
        if sys.version_info >= (3,0): # Python 3 returns
            try:
                # Test ISO format
                endtimedate = datetime.fromisoformat(endtimedate)
                endtime = end.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                nimP.warning("End date/time format not supported, please use ISO format: 2011-11-04 00:05:23")
                endtimedate = ''
        else:
            # Python 2
            # Supported formats:
            # 2011-11-04 00:05:23 -> Used by NIM
            # 2011-11-04T00:05:23
            if endtimedate.count('.') > 0:
                endtimedate = endtimedate.split('.')[0] # Remove miliseconds. After .
            try:
                #Test ISO format
                endtimedate = datetime.strptime(endtimedate, "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                try :
                    #Test ISO format 2
                    endtimedate = datetime.strptime(endtimedate, "%Y-%m-%dT%H:%M:%S")
                    endtimedate = datetime.strptime( str(endtimedate).replace("T", " "), "%Y-%m-%d %H:%M:%S" )
                except ValueError as e:
                    nimP.warning("End date/time format not supported, please use ISO format: 2011-11-04 00:05:23")
                    endtimedate = ''
            if endtimedate:
                endtime= endtimedate.strftime("%Y-%m-%d %H:%M:%S")

    if starttimedate and endtimedate:
        # Calculate total time and average time for render
        # starttime = datetime.strptime( starttimedate.split('.')[0], "%Y-%m-%dT%H:%M:%S" ) # remove microseconds
        # endtime = datetime.strptime( endtimedate.split('.')[0], "%Y-%m-%dT%H:%M:%S" ) # remove microseconds
        rendertime = endtimedate - starttimedate
        rendertimestr = str(rendertime.seconds)
        if nframes:
            avgtime = rendertime // nframes
            avgtimestr = str(avgtime.seconds)

    # XXX: for AOVs follow file metadata extra elements to get all the paths and output dirs
    # print("Task for render: %s"%task['taskID'])
    res = nimAPI.add_render( jobID=jobid, itemType=parent, taskID=int(task['taskID']), fileID=int(fileInfo['fileID']), \
        renderKey=renderkey, renderName=rendername, renderType=rendertype, renderComment=comment, \
        outputDirs=(outdir,), outputFiles=(path,), elementTypeID=elementTypeID, start_datetime=starttimedate, end_datetime=endtimedate, \
        avgTime=avgtimestr, totalTime=rendertimestr, frame=nframes )
    if res['success'] == 'true' and icon and os.path.exists(icon):
        resicon = nimAPI.upload_renderIcon( renderID=int(res['ID']), img=icon) 
        if verbose:
            pprint(resicon)
    if res['success'] == 'true':
        updateelmt_result = nimAPI.update_element( ID=int(elementInfo['ID']), renderID=int(res['ID']))
        if updateelmt_result['success'] != 'true':
            if verbose:
                nimP.error("Error linking element to task")
            res['success'] = False
            res['msg']     = "Error linking element to task"
            return res if not plain and not jsonout else False
        res['success'] = True
        nimP.info("Render %s in %s %s published"%(filename, parent.lower(), parentname))
    else:
        nimP.error("Couldn't published render %s in %s %s"%(filename, parent.lower(), parentname))
        
    if verbose:
        pprint( res )
    
    return res

def createRender(fileID='', filename='', job='', userid ='', parent="shot", parentID="", renderkey='', comment='', rendertype='', starttimedate='', endtimedate='', doreview=True, reviewtype=reviewType.DAILY, verbose=False):
    '''
    Do all steps to create all the elements needed to get a render properly published, and log them into NIM
    This is the function to call to get a published path, with pubpath(), and create a render for it.

    Render Publish Stages
    ---------------------
    - Create Icon
    - Publish render from Filename or fileID, if there is a task available in the shot/asset
    - Link Element associated to the File to the former render
    - Create Review
    - Publish Review
    - Link render to review

    Parameters
    ----------
    fileID : int
        If passed all info about the render will be gather from the published File. filename, userid, job, parent and parentID wont be needed.
    filename : str
        Filename of element to query. Name convention: [SHOT|ASSET]__[TASK]__[TAG]__[VER].####.ext. Not needed if fileID is passed.
    userid    : int
        User ID who owns the published item.Not needed if fileID is passed.
    job : str
        number or ID for job .Not needed if fileID is passed.
    parent : str
        Parent for publish element:SHOT or ASSET.Not needed if fileID is passed.
    parentID : str
        Shot or Asset ID .Not needed if fileID is passed.
    renderkey : str
        Render ID in the farm. For instance from Deadline wit will be Deadline's job id.
    comment   : str
        Render comment.
    rendertype   : str
        Render source, Nuke, Mantra, Vray, etc ....
    frames   : str
        Frames list: 1001-1100
    starttimedate   : str
        Render start in UTC
    endtimedate      : str
        Render end in UTC
    reviewtype      : reviewType
        Review type: reviewType.DAILY(1), reviewType.EDIT(2), reviewType.REF(3)
    doreview : bool
        Create review movie and publish it with the render
    verbose : bool
        Output extra information

    Returns
    -------
    dict
        Dictionary with keys:
        - success: bool
        - msg: string with error message
        - ID: string with renderID number
        - reviewID: render review ID
    '''
    ver = 0
    parentname = ""
    jobid, jobnumber = 0, ""
    res = {'success' : False}
    fileInfo = None

    # userid
    if not userid:
        # FIXME: apparently when calling to this from nuke it cant get the user
        # correctly
        myuser = nimAPI.get_user()
        if not myuser:
            nimP.error("Can't get user from NIM. Is user correctly setup?")
            return res
        userid = int(nimAPI.get_userID(myuser))

    if not fileID:
        if not filename:
            if verbose:
                nimP.error("Need to provide a FileID or a filename in order to publish a render from them")
            res['success'] = False
            res['msg']     = "Need to provide a FileID or a filename in order to publish a render from them"
            return res
        
        if not userid or not nimUtl.getuserName(userid):
            nimP.error("Wrong user id: %d"%userid)
            
        # (base, shotname, task, tag, ver) = nimUtl.splitName( filename )
        fileparta = nimUtl.splitName( filename )
        if not parentID:
            # Use shot/asset name from file name if not provided
            parentID = fileparts['shot']

        if (isinstance(parentID, int) and parentID>0) or (isinstance(parentID, str) and len(parentID) > 0):
            if not isinstance(parentID, int) and not parentID.isnumeric():
                if job:
                    (jobid, jobnumber) = nimUtl.getjobIdNumberTuple( job )
                    if not jobid:
                        sys.exit()
                elif not job or not jobid:
                    if verbose:
                        nimP.error("If parent is defined as a name, a job number or ID need to be provided")
                    res['success'] = False
                    res['msg']     = "If parent is defined as a name, a job number or ID need to be provided"
                    return res
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
            if verbose:
                nimP.error("Need to provide a parent name or ID. It will be a shot name or ID, asset name or ID, etc ...")
            res['success'] = False
            res['msg']     = "Need to provide a parent name or ID. It will be a shot name or ID, asset name or ID, etc ..."
            return res


        # Check naming convention, if shot/asset name in basename doesn't match provided parentname then error
        if fileparts['shot'] != parentname:
            if verbose:
                nimP.error("Wrong basename name. Basename %s shot/asset and selected shot/assset are different: %s / %s"%(fileparts['base'], fileparts['shot'], parentname))
            res['success'] = False
            res['msg']     = "Wrong basename name. Basename %s shot/asset and selected shot/assset are different: %s / %s"%(fileparts['base'], fileparts['shot'], parentname)
            return res

        if parent.upper() == 'SHOT':
            vers = nimAPI.get_vers( shotID=id, basename=fileparts['base'])
        else:
            vers = nimAPI.get_vers( assetID=id, basename=fileparts['base'])
        if vers:
            # pprint(vers)
            for verfile in vers:
                if int(verfile['version']) == fileparts['ver']:
                    fileInfo = verfile
                    break
    else:
        # Grab just published info
        info = nimAPI.get_verInfo( fileID )
        fileInfo = info[0]


    # Retrieve file info
    # print("File version to publish render to:")
    # pprint(fileInfo)
    fileid = int(fileInfo['fileID'])
    path = fileInfo['filepath']
    name =  fileInfo['filename'] 
    # (base, shotname, task, tag, ver) = nimUtl.splitName(name)
    fileparts = nimUtl.splitName(name)
    rendername = fileparts['base'] + "__" + "v%s"%str(fileparts['ver']).zfill(padding)
    pid = int(fileInfo['parentID'])
    parent = fileInfo['fileClass'].lower()
    if parent.upper() == 'SHOT':
        parentname = nimAPI.get_shotInfo( shotID=pid)[0]['shotName']
    else:
        parentname = nimAPI.get_asseetInfo( shotID=pid)[0]['assetName']
    outdir = os.path.dirname(path)
    tasktype = int(fileInfo['task_type_ID'])
    # Check availability:
    available = fileInfo['customKeys']['State'] == 'Available'
    if not available:
        nimP.warning("File is not set as available. ther could be errors: %s, State: %s"%(name, fileInfo['customKeys']['State']))
    elementInfo = nimAPI.find_elements( name=fileInfo['filename'], assetID=pid if parent.upper()=='ASSET' else '', shotID=pid if parent.upper()=='SHOT' else '')
    if elementInfo:
        elementInfo=elementInfo[0]
    else:
        if verbose:
            nimP.error("Couldn't find an element for the render: %s"%name)
        res['success'] = False
        res['msg'] = "Couldn't find an element for the render: %s"%name
        return res
    if elementInfo['taskID']:
        taskid = int(elementInfo['taskID']) 
    else:
        taskid = 0
    
    # print("Render Element:")
    # pprint(elementInfo)

    renderid = 0
    if taskid:
        # Can only publish render if there is an available task
        # Create icon
        # FIXME: icon creation not working in the farm
        if verbose:
            nimP.info("Create render icon ..")
        icon = createRenderIcon( elementInfo )
        if not icon:
            res['msg'] = "Error creating render icon for %s"%rendername
            res['success'] = False
            return res
        # icon=""

        # Publish render
        if verbose:
            nimP.info("Publish render ....")
        res = pubRender(fileID=fileid, userid=userid, renderkey=renderkey, comment=comment, rendertype=rendertype, starttimedate=starttimedate, endtimedate=endtimedate, icon=icon, verbose=verbose)
        if not res['success']:
            res['success'] = False
            res['msg']     = "Error publishing render %s in %s %s"%(fileparts['base'], fileparts['shot'], parentname)
            return res
        renderid = int(res['ID'].encode('ascii'))
        res['ID'] = renderid
    else:
        nimP.warning("Couldn't find a task %s for %s %s. Render item won't be published."%(nimUtl.gettasksTypesIDDict()[tasktype], parent, parentname))
            

    if doreview:
        # Create draft movie
        if verbose:
            nimP.info("Create render review ......")
        frange   = elementInfo['startFrame'] + "-" + elementInfo['endFrame']
        draft    = createDraftMovie( path, str(frange))
        if not draft:
            return False

        # Create review
        draftPosix = toPosix(draft)
        # Add review to render item or to parent item
        keywords = [nimUtl.getelementsIDDict()[int(elementInfo['elementTypeID'])]]
        if renderid:
            res_review = nimAPI.upload_reviewItem( itemID=renderid, itemType='render', userID=userid, path=draftPosix, reviewItemTypeID=reviewtype, name=rendername, description=comment, keywords=keywords) 
        else:
            res_review = nimAPI.upload_reviewItem( itemID=pid, itemType=parent.lower(), userID=userid, path=draftPosix, reviewItemTypeID=reviewtype, name=rendername, description=comment, keywords=keywords) 
        if res_review:
            p = re.compile('^.+"ID":"\(\d+\)".+$')
            m = p.match(res_review)
            if m:
                res['reviewID'] = int(m.group(1))
            
    if not res:
        res['success'] = False
        res['msg']     = "Error publishing review for render %s in %s %s"%(fileparts['base'], fileparts['shot'], parentname)
        return res

    res['success'] = True
    res['msg'] = "Render %s created in %s %s"%(rendername, parent, fileparts['shot'])

    return res

def pubReview(fileID, reviewpath, taskID=None, renderID=None, renderkey=None, userID=None, reviewtype=reviewType.NOTYPE, comment=""):
    '''
    Publish review movie.
    A fileID for the render files needs 

    Where The Review is Published
    -----------------------------
    A review in NIM can be published to a parent entity in the project, like job, show, asset, show or task.
    It can also be published linked to a render item. Similar to tasks, renders are published relative to a task, shot or asset.
    Another way to link a review to a render item is using a renderkey. This is usually the job id in the farm and is used to link
    renders to reviews when they are published in different tasks in the farm.
    When a render finished a new job to generate the review movie is spawn, but probably the render is not yet published, so to create a link between a revciew movie that is in the 
    process of making and a render that will be published shortly the job id is used as a link between the different tasks in the farm.
    When the review is published it can find the render item if the former was published with the renderkey information.

    Usually reviews are published to a task, providing a taskid, a render, providing a renderid and if any of the two area passed to this function it will use the parent of the file
    published using fileID to log the review to the shot or asset where the file was published.

    In the farm it is always good to provide a renderkey to ensure review will be correctly linked to our render.
    createRender() also has a renderkey parameter in order to publish the render item with this information.

     Parameters
    ----------
    fileID : int
        FileID for the render that created the review
    reviewpath : str
        Path to review movie to publish
    taskID : int
        ID for task to publish to. If not published then the preview will be published relative to the FileID parent (shot,asset, show)
    renderID : int
        ID for render item to publish to. If not published then the preview will be published relative to the FileID parent (shot,asset, show)
    renderkey : str
        Render Job ID used to identify render published items. If provided the review item will be linked to a render item that was published using the same render key.
    comment : str
        Review comment/description
    
    Return
    ------
    reviewid : int
        Review ID or False if error
    '''
    info = nimAPI.get_verInfo( fileID )
    if not info:
        nimP.error("Can't retrieve information from FileID: %d"%fileID)
    fileInfo = info[0]
    # print("File Info:")
    # pprint(info)
    path = fileInfo['filepath']
    name =  fileInfo['filename'] 
    # (base, shotname, task, tag, ver) = nimUtl.splitName(name)
    fileparts = nimUtl.splitName(name)
    rendername = fileparts['base'] + "__" + "v%s"%str(fileparts['ver']).zfill(padding)
    pid = int(fileInfo['parentID'])
    parent = fileInfo['fileClass'].lower()
    if parent.upper() == 'SHOT':
        parentname = nimAPI.get_shotInfo( shotID=pid)[0]['shotName']
    else:
        parentname = nimAPI.get_asseetInfo( shotID=pid)[0]['assetName']
    outdir = os.path.dirname(path)
    tasktype = int(fileInfo['task_type_ID'])
    if not userID:
        userID = int(fileInfo['userID'].encode('ascii'))
        username = nimUtl.getuserName(userid)
    # Check availability:
    available = fileInfo['customKeys']['State'] == 'Available'
    if not available:
        nimP.warning("File is not set as available. ther could be errors: %s, State: %s"%(name, fileInfo['customKeys']['State']))
    elementInfo = nimAPI.find_elements( name=fileInfo['filename'], assetID=pid if parent.upper()=='ASSET' else '', shotID=pid if parent.upper()=='SHOT' else '')
    if elementInfo:
        elementInfo=elementInfo[0]
    else:
        if verbose:
            nimP.error("Couldn't find an element for the render: %s"%name)
        res['success'] = False
        res['msg'] = "Couldn't find an element for the render: %s"%name
        return res
    if elementInfo['taskID']:
        taskid = int(elementInfo['taskID']) 
        if not taskID:
            taskid = taskid
    else:
        taskid = 0

    keywords = [nimUtl.getelementsIDDict()[int(elementInfo['elementTypeID'])]]
    if renderID:
        res_review = nimAPI.upload_reviewItem( itemID=renderID, itemType='render', renderKey=renderkey, userID=userID, path=reviewpath, reviewItemTypeID=reviewtype, name=rendername, description=comment, keywords=keywords) 
    elif taskID:
        res_review = nimAPI.upload_reviewItem( itemID=taskID, itemType='task', renderKey=renderkey, userID=userID, path=reviewpath, reviewItemTypeID=reviewtype, name=rendername, description=comment, keywords=keywords) 

    else:
        res_review = nimAPI.upload_reviewItem( itemID=pid, itemType=parent.lower(), renderKey=renderkey, userID=userID, path=reviewpath, reviewItemTypeID=reviewtype, name=rendername, description=comment, keywords=keywords) 

    # Return review ID
    # print("Review result:")
    # print(res_review)
    if res_review:
        p = re.compile('^.+"ID":"(\d+)".+$')
        m = p.match(res_review)
        if m:
            # print("Return review ID: %d"%int(m.group(1)))
            return int(m.group(1))
        else:
            nimP.warning("Can't get review ID from upload query:")
            nimP.warning(res_review)
            return True

    return False


def pubImport(job, path, name='', parent='shot', parentID="", task="", element='', file="",user="", version=0, start=1001, end=1001, handles=0, overwrite=pubOverwritePolicy.NOT_ALLOW, 
              comment='', asrender=False, reviewtype=reviewType.DAILY, plain=False, jsonout=False, profile=False, dryrun=False, verbose=False):
    '''
    Copy elements data from an arbitrary location into the project according to the publishing details

    Parameters
    ----------
    job : str
        number or ID for job
    path : str
        Path to data to publish. I can be a static file or a sequence (User #### for padding)
    name : str
        Alternative name for publish item when importing to job.
    parent : str
        Parent for this publish element. Where the element will be published. By default 'shot'
    parentID : str
        ID or name if parent entity. Name of shot, asset or show to render to
    task : str
        name or ID of task type to list items from.
    element : str
        Element type of published item. Empty if item is not an element
    file : str
        File type. Usually DCC scene type. Empty if item is not a scene file.By default ""
    user : str
        User who owns the published item. If not provided use current user
    version : int
        Publish version. 0 to automatically up and publish to last version
    start : int
        Start frame.
    end : int
        End frame.
    handles : int
        Frame handles.
    overwrite : pub.pubOverwritePolicy
        Overwrite policy. Whether or not allow to reuse pub elements/files
    comment : str
        Publish comment.
    asrender : bool
        create render elements and publish render and review items
    reviewtype      : reviewType
        Review type: reviewType.DAILY(1), reviewType.EDIT(2), reviewType.REF(3)
    plain : bool
        Output in plain text format.
    jsonout : bool
        Output in JSON format
    profile : bool
        Test different stages performance and output results
    dryrun : bool
        Go thorough the whole process, return information of actions to take but don't modify anything
    verbose : bool
        Output extra information

    Returns
    -------
    bool
        True if no errors
    '''

    ver = 0
    parentname = ""
    id = 0
    jobid, jobnumber = 0, ""
    res = {'success' : False, 'msg' : None}
    isseq = False
    files = []

    # check path and get absolute path. This allows to pass a relative path to current location
    (filepath, filename) = os.path.split( path )
    (isvalid, isseq) = validateFilename( filename )
    abspath = os.path.abspath( path )
    parts = path.split('.')
    
    # Check files path
    if not isseq :
        if os.path.exists(path):
            files.append(path)
    else:
        parts[1] = '*'
        pat = '.'.join(parts)
        files = glob( pat )
    if not files:
        nimP.error("Can't files file/s for specified path: %s"%path)
        res['msg'] = "Can't files file/s for specified path: %s"%path
        return res

    if job:
        (jobid, jobnumber) = nimUtl.getjobIdNumberTuple( job )
        if not jobid:
            res['msg'] = "Cne't get id for job: %s"%job
            return res
    else:
        res['msg'] = "Please select a job to publish to"
        return res

    if not parentID:
        res['msg'] = "Need to provided a shot/asset name to publish to"
        return res

    if not isinstance(parentID, int) and not parentID.isnumeric():
        if not jobid:
            res['msg'] = "If parent is defined as a name, a job number or ID need to be provided"
            return res
        parentname = parentID
        if parent.upper() == 'SHOT':
            id = nimUtl.getshotIdFromName( jobid, parentname )
        else:
            id = nimUtl.getassetIdFromName( jobid, parentname )
            
        if not id:
            res['msg'] = "Couldn't find shot/asset %s in %s "%(parentname, jobnumber)
            return res
    else:
        id=int(parentID)
        if parent.upper() == 'SHOT':
            parentname = nimAPI.get_shotInfo( shotID=id)[0]['shotName']
        else:
            parentname = nimAPI.get_assetInfo( shotID=id)[0]['assetName']

    jobloc = nimUtl.getjobLocation(jobid)
    if not jobloc:
        return res
    baseloc = elementTypeFolder( element, parent, id )
    if baseloc:
        basepath = nimAPI.get_paths( item=parent, ID=id )['root']
        baseloc = os.path.join(basepath, baseloc)
    if not baseloc:
        res['msg'] = "Can't get a base path for element %s in %s %s"%(element, parent.lower(), parentname)
        return res
    baseloc = os.path.join(os.path.dirname(jobloc), baseloc) # Remove job number folder from jobloc, is already included at the start of baseloc
        
    # Get name
    if not name:
        nimP.warning("Publish name not provided, filename will be used: %s"%filename)
        name = filename.split('.')[0]
    # Create basename
    basename = buildBasename( parentname, task, name)
    if verbose:
        nimP.info("Basename: %s"%basename)

    #Get version from basename
    if not version:
        version = getNextPublishVer ( basename, parent=parent.upper(), parentID=id)
        nimP.info("Find next version for %s: %d"%(basename, version))
    if verbose:
        nimP.info("Version to publish: %d"%version)

    # Get target path according to name convention
    pubpath = publishOutputPath ( baseloc, shot=parentname, name=name, ver=version, task=task,  ext=parts[-1], isseq=isseq )
    if verbose:
        nimP.info("Pub path: %s"%pubpath)

    # Copy data to target location with correct name
    pubdirname = os.path.dirname(pubpath)
    try:
        os.makedirs( pubdirname, mode=user_mask, exist_ok=True)
    except Exception as e:
        res['msg'] = str(e)
        return res
    if not isseq:
        try:
            shutil.copy( path, pubpath )
        except Exception as e:
            res['msg'] = str(e)
            return res
        if verbose:
            print("File %s\n\t->Imported into: %s"%(path, pubpath))
    else:
        nimP.info("Copying files into: %s"%os.path.dirname(pubpath))
        for f in files:
            framestr = f.split('.')[1] #Assume string before extension is the frame, this is our name convention
            dest = pubpath.replace('####', framestr)
            try:
                shutil.copy( f, dest )
            except Exception as e:
                res['msg'] = str(e)
                return res
            if verbose:
                print("File %s\n\t->Imported into: %s"%(f, dest))

    # Call to pubPath() to publish it
    pubres = pubPath(pubpath, user, comment=comment, start=start, end=end, handles=handles, overwrite=overwrite, state=pubState.AVAILABLE , plain=plain, jsonout=jsonout, profile=profile, dryrun=dryrun, verbose=verbose)
    if not pubres['success']:
        res['msg'] = pubres['msg']
        return res

    # Create render if needed
    if asrender:
        pubrender = createRender( fileID=pubres['fileID'], userid=user, comment=comment, reviewtype=reviewtype, verbose=verbose)
        pprint(pubrender)

    res['success'] = True
    return res
#
# UI
#
if 'PySide2.QtGui' in sys.modules or 'Pyside.QtGui' in sys.modules or 'PyQt4.QtGui' in sys.modules:
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
            if builtin_mod_available:
                buttons_labels_idx = zip(self.labels, list(range(len(self.labels))))
            else:
                buttons_labels_idx = zip(self.labels, range(len(self.labels)))
                
            for label, idx in buttons_labels_idx:
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
            self.value = int(data)
            self.close()
            return

        def click_details( self ) :
            'Show details text'
            target = self.sender()  # <<< get the event target, i.e. the button widget
            self.detail.show()
            # data = target.my_own_data  # <<< get your own property
            # self.value = int(data)
            # self.close()
            return
        
        def btn(self) :
            'Returns the button that was pushed'
            return self.value

        def CloseEvent( self, event):
            print("Closing ....")
        
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
