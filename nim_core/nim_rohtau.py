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
import os
import platform
import re
import subprocess
from datetime import datetime


from .import version 
from .import winTitle 

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
            print "NIM: Failed to UI Modules - UI"

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
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

    return True

def publishOutputPath ( baseloc, shot, name, ver, task,  ext='exr', subtask='', layer='', cat='', subfolder='', isseq=False, format='houdini', only_name=False, only_loc=False, force_posix=False  ):
    '''
    Build output path for a publish element

    Supported app output formats:
    - Houdini (houdini)
    - Nuke (nuke)

    If we need to store temp files for the render we can use the subfolder option. for instance if we need to store IFD files for Mantra
    we can set subfolder to be 'ifd', extension to be 'ifd', then the file path will be a subfolder in the output location called ifd and the files will have the ifd extension.

    Arguments:
        baseloc {str} -- base directory for  the files
        shot {str} -- shot/asset name for the render job
        name {str} -- element name
        ver {int} -- element version
        task {str} -- task assigned to render job

    Keyword Arguments:
        ext {str} -- element file type extension (default: {'exr'})
        subtask {str} -- extra task definition for more granular setups (default: {''})
        layer {str} -- another extra identifier to group elements, usually by distance or "importance" in the shot.(default: {''})
        cat {str} -- render category, useful to distinguish between final renders and different tests and QD (default: {''})
        subfolder {str} -- used to save temp or auxiliary files for a render. It designates subfolder in the output path to store the files.
        isseq {bool} -- define whether or not the path is a sequence or single file
        format {str} -- output format for host app. this is mostly needed because every app uses a different way of setting padding for sequences.
        only_name {bool} -- just output the file base name without padding or extension. (default: {False})
        only_loc {bool} -- just output the base directory for the output files. (default: {False})
        force_posix {bool} -- force using Posix format even in a Windows environment (default: {False})

    Returns:
        str -- complete path for the element
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
            if format == 'houdini':
                name += ".$F4.%s"%ext
            elif format == 'nuke':
                name += ".%"+"04d.%s"%ext
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
    ro_mask = 0777 ^ (stat.S_IWRITE | stat.S_IWGRP | stat.S_IWOTH)
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


class DisplayMessage( QtGui.QDialog ) :

    def __init__(self, msg, title="Display Message", buttons=("Ok",), default_button=0, details="", parent=None) :
        '''
        Inspired in houdini's diplsayMessage, simple modal dialog to present a message and have the user
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
        for label, idx in zip(self.labels, range(len(self.labels))):
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
