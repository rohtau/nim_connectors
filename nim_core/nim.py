#!/usr/bin/env python
#******************************************************************************
#
# Filename: nim.py
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

import ntpath, os, traceback
import sys
from sys import path
from pprint import pprint

if sys.version_info >= (3,0):
    from . import nim_api as Api
    from . import nim_file as F
    from . import nim_prefs as Prefs
    from . import nim_print as P
else:
    import nim_api as Api
    import nim_file as F
    import nim_prefs as Prefs
    import nim_print as P

from .import version 
from .import winTitle


from .import version 
from .import winTitle 


class NIM( object ) :
    
    def __init__(self) :
        'Initializes the NIM attributes'
        super( NIM, self ).__init__()
        self.nim={}
        
        #  Store preferences :
        self.prefs=Prefs.read()
        
        #  Store the different GUI elements to be populated :
        self.elements=['job', 'asset', 'show', 'shot', 'filter', 'element', 'task', 'base', 'ver']
        self.print_elements=['job', 'asset', 'show', 'shot', 'filter', 'element', 'task', 'basename', 'version']
        self.comboBoxes=['job', 'asset', 'show', 'shot', 'filter', 'task']
        self.listViews=['base', 'ver']
        
        #  Instantiate dictionary of settings :
        for elem in self.elements :
            self.clear( elem )
        
        #  Make image attributes :
        for elem in ['asset', 'shot'] :
            self.nim[elem]['img_pix']=''
            self.nim[elem]['img_label']=''
        
        #  Set file attributes :
        # self.nim['file']={'path': '', 'filename': '', 'dir': '', 'basename': '', 'compPath': '', 'version': ''}
        # Add renderPath and platesPath
        self.nim['file']={'path': '', 'filename': '', 'dir': '', 'basename': '', 'jobPath': '', 'shotPath': '', 'compPath': '', 'renderPath': '', 'platesPath': '', 'version': ''}
        self.set_filePath()
        
        #  Extra NIM attributes :
        for elem in ['comment', 'fileExt', 'tag'] :
            self.nim[elem]={'name': '', 'input': None}
        self.nim['server']={'name':'', 'path': '', 'input':'', 'ID': '', 'Dict': ''}
        self.nim['fileExt']['fileType']=''
        self.nim['app']=F.get_app()
        self.nim['class']=None
        self.nim['mode']=None
        self.nim['pub']=False
        
        #  Attempt to set User information :
        self.nim['user']={'name': '', 'ID': '' }
        if self.prefs :
            if 'NIM_User' in list(self.prefs.keys()) :
                self.nim['user']['name']=self.prefs['NIM_User']
                if self.nim['user']['name'] :
                    self.nim['user']['ID']=Api.get_userID( user=self.nim['user']['name'] )

        # Publishing elements types:
        self.nim['elements'] = Api.get_elementTypes()

        # NIM version
        self.nim['nimver'] = version # Init nim version on object construct
        
        #  App Specific :
        if self.nim['app']=='C4D' :
            #  Group ID's :
            self.grpIDs={ 'main': 101, 'top': 102, 'jobAsset': 103, 'tab': 104, 'job': 105,
                'asset': 106, 'showShot': 107, 'taskBase': 108, 'ver': 109, 'btn': 110 }
            #  Input ID's :
            self.inputIDs={ 'job': 200, 'server': 201, 'asset': 202, 'show': 203, 'shot': 204, 'filter': 205,
                'task': 206, 'base': 207, 'tag': 208, 'comment': 209, 'ver': 210, 'verFilepath': 211,
                'verUser': 212, 'verDate': 213, 'verComment': 214 , 'checkbox': 215}
            #  Text ID's :
            self.textIDs={ 'job': 300, 'server': 301, 'asset': 302, 'show': 303, 'shot': 304, 'filter': 305,
                'task': 306, 'base': 307, 'tag': 308, 'comment': 309, 'ver': 310, 'verFilepath': 311,
                'verUser': 312, 'verDate': 313, 'verComment': 314 }
            #  Lowest Menu IDs :
            self.start_menuIDs={'job': 1000, 'asset': 2000, 'show': 3000, 'shot': 4000, 'filter': 5000,
                'task': 6000, 'base': 7000, 'ver': 8000}
            #  Menu ID's :
            self.menuIDs={ 'job': {}, 'asset': {}, 'show': {}, 'shot': {}, 'filter': {}, 'task': {}, 'base': {}, 'ver': {} }
            #  Button ID :
            self.btnID=10070
            self.cancelBtnID=10071
            
        
        return
    
    def Print( self, indent=4, debug=False ) :
        'Prints the NIM dictionary'
        
        if not debug :
            P.info( ' '*indent+'{' )
            if self.nim['server']['path'] :
                P.info( ' '*indent*2+'Server Path = "%s"' % self.nim['server']['path'] )
            if self.nim['server']['name'] :
                P.info( ' '*indent*2+'  Name = "%s"' % self.nim['server']['name'] )
            if self.nim['server']['ID'] :
                P.info( ' '*indent*2+'  ID = "%s"' % self.nim['server']['ID'] )
            if self.nim['server']['Dict'] :
                P.info( ' '*indent*2+'  Dict = "%s"' % self.nim['server']['Dict'] )
            if self.nim['server']['input'] :
                P.info( ' '*indent*2+'  Input = "%s"' % self.nim['server']['input'] )
            for elem in self.elements :
                P.info( ' '*indent*2+'%s = "%s"' % (self.get_printElem( elem ), self.name( elem )) )
                if self.Input( elem ) :
                    P.info( ' '*indent*2+'  Input = %s' % self.Input( elem ) )
                if self.ID( elem ) :
                    P.info( ' '*indent*2+'  ID = "%s"' % self.ID( elem ) )
                if self.Dict( elem ) :
                    P.info( ' '*indent*2+'  Dict = %s' % self.Dict( elem ) )
                if elem=='task' :
                    P.info( ' '*indent*2+'  Task Folder = "%s"' % self.taskFolder() )
            P.info( ' '*indent*2+'tab = "%s"' % self.nim['class'] )
            P.info( ' '*indent+'}' )
        elif debug :
            P.debug( ' '*indent+'{' )
            if self.nim['server']['name'] :
                P.debug( ' '*indent*2+'Server = "%s"' % self.nim['server']['name'] )
            if self.nim['server']['path'] :
                P.debug( ' '*indent*2+'  Path = "%s"' % self.nim['server']['path'] )
            if self.nim['server']['ID'] :
                P.debug( ' '*indent*2+'  ID = "%s"' % self.nim['server']['ID'] )
            if self.nim['server']['Dict'] :
                P.debug( ' '*indent*2+'  Dict = "%s"' % self.nim['server']['Dict'] )
            if self.nim['server']['input'] :
                P.debug( ' '*indent*2+'  Input = "%s"' % self.nim['server']['input'] )
            for elem in self.elements :
                P.debug( ' '*indent*2+'%s = "%s"' % (self.get_printElem( elem ), self.name( elem )) )
                if self.Input( elem ) :
                    P.debug( ' '*indent*2+'  Input = %s' % self.Input( elem ) )
                if self.ID( elem ) :
                    P.debug( ' '*indent*2+'  ID = "%s"' % self.ID( elem ) )
                if self.Dict( elem ) :
                    P.debug( ' '*indent*2+'  Dict = %s' % self.Dict( elem ) )
                if elem=='task' and self.taskFolder() :
                    P.debug( ' '*indent*2+'  Task Folder = "%s"' % self.taskFolder() )
            P.debug( ' '*indent*2+'tab = "%s"' % self.nim['class'] )
            P.debug( ' '*indent+'}' )
        
        return
    
    def clear( self, elem='job' ) :
        'Clears the dictionary of a given element'
        label, pic='', ''
        
        if elem in ['asset', 'shot'] and elem in list(self.nim.keys()) :
            if 'img_pix' in list(self.nim[elem].keys()) :
                pic=self.nim[elem]['img_pix']
            if 'img_label' in list(self.nim[elem].keys()) :
                label=self.nim[elem]['img_label']
        if elem in list(self.nim.keys()) and 'input' in list(self.nim[elem].keys()) and self.nim[elem]['input'] :
            #  Preserve job dictionary, if it exists :
            if elem=='job' and len(self.nim[elem]['Dict']) :
                self.nim[elem]={'name': '', 'ID': None, 'Dict': self.nim[elem]['input'], \
                    'input': self.nim[elem]['input'], 'inputID': None}
            else :
                self.nim[elem]={'name': '', 'ID': None, 'Dict': {}, 'input': self.nim[elem]['input'], 'inputID': None}
        else :
            self.nim[elem]={'name': '', 'ID': None, 'Dict': {}, 'input': None, 'inputID': None}
        #  Re-set image pixmap and label :
        if elem in ['asset', 'shot'] and elem in list(self.nim.keys()) :
            if pic : self.nim[elem]['img_pix']=pic
            if label : self.nim[elem]['img_label']=label
        #  Add Task folder :
        if elem=='task' :
            self.nim[elem]['folder']=''
        #  Initiate Filter :
        if elem=='filter' :
            self.nim[elem]['name']='Work'
        
        return
    
    def ingest_prefs(self) :
        'Sets NIM dictionary from preferences'
        self.app=F.get_app()
        self.prefs=Prefs.read()
        
        if not self.prefs :
            return False

        P.info( 'Preferences being read...' )

        #  Set User Information :
        user=self.prefs['NIM_User']
        userID=Api.get( sqlCmd={ 'q': 'getUserID', 'u': user}, debug=False )
        if userID :
            if type(userID)==type(list()) and len(userID)==1 :
                userID=userID[0]['ID']
            try : self.nim['user']={'name': user, 'ID': str(userID) }
            except :
                self.nim['user']={'name': '', 'ID': ''}
                P.warning( 'Unable to set User information in NIM!' )
            
            #  Get Show/Shot Prefs :
            try :
                self.set_name( elem='job', name=self.prefs[self.app+'_Job'] )
                self.set_name( elem='asset', name=self.prefs[self.app+'_Asset'] )
                self.set_tab( _type=self.prefs[self.app+'_Tab'] )
                self.set_name( elem='show', name=self.prefs[self.app+'_Show'] )
                self.set_name( elem='shot', name=self.prefs[self.app+'_Shot'] )
                self.set_name( elem='filter', name=self.prefs[self.app+'_Filter'] )
                self.set_name( elem='task', name=self.prefs[self.app+'_Task'] )
                self.set_name( elem='base', name=self.prefs[self.app+'_Basename'] )
                self.set_name( elem='ver', name=self.prefs[self.app+'_Version'] )
            except :
                P.error( 'Sorry, unable to get NIM preferences, cannot run NIM GUI' )
                P.error( '    %s' % traceback.print_exc() )
                win.popup( title='NIM Error', msg='Sorry, unable to get NIM preferences, cannot run NIM GUI' )
                return False
            return self
        else :
            return False
    
    def ingest_filePath( self, filePath='', pub=False, checkfile=True ) :
        '''
        Sets NIM dictionary from current file path

        rohtau Name convention
        DCC Scene Files:
        [JOB]/[work|build]/[SHOT|ASSET]/task/[TASK]/[TAG]/[APP]/
        [SHOT|ASSET]__[TASK]__[TAG]__[VER].ext

        Elements:
        [JOB]/[work|build]/[SHOT|ASSET]/[ELEMPATH]/[TASK]/[ELEMNAME]__[CAT]/[VER]/
        [SHOT|ASSET]__[TASK]__[TAG]__[VER].####.ext
        '''
        
        jobFound, assetFound, showFound, shotFound=False, False, False, False
        taskFound, basenameFound, versionFound=False, False, False
        elementFound, potentialElement, potentialTask= False, False, False
        jobs, assets, shows, shots, tasks, basenames, version={}, {}, {}, {}, {}, {}, {}
        
        # print("Starting Dict")
        # pprint(self.get_nim())

        #  Get and set jobs dictionary :
        jobsfolders = Api.get_jobs( userID=self.nim['user']['ID'], folders=True )
        jobsfolders = { key.decode():value.decode() for (key,value) in jobsfolders.items()} # The output from Api is in bytes no string
        jobs        = Api.get_jobs( userID=self.nim['user']['ID'], folders=False )
        jobs        = { key.decode():value.decode() for (key,value) in jobs.items()}

        self.set_dict('job')
        
        #  Verify file path structure :
        if not filePath :
            filePath=F.get_filePath()
        if not filePath :
            P.debug( 'File must be saved with a filename that exists in NIM.' )
            return None
        if not os.path.isfile( os.path.normpath( filePath ) ) and os.path.isfile( \
                os.path.normpath( filePath ) ) :
            filePath=os.path.normpath( filePath )
        if checkfile and  not os.path.isfile( filePath ) :
            P.error( 'Sorry, the given file path doesn\'t appear to exist...' )
            P.error( '    %s' % filePath )
            return None
        
        P.debug( 'Attempting to gather API information from the following file path...' )
        P.debug( '    %s' % filePath )
        
        #  Tokenize file path :
        if len(filePath.split( '/' )) > len(filePath.split( '\\' )) :
            toks=filePath.split( '/' )
        elif len(filePath.split( '/' )) < len(filePath.split( '\\' )) :
            toks=filePath.split( '\\' )
            
        #  Initialize tab :
        self.set_tab( _type=None )
        # Init filepath
        self.set_filePath(filePath)

        # Find Job :
        for tok in toks :
            if not jobFound :
                # Job
                for job in jobsfolders :
                    jobfolder = job.split()[2].strip()
                    jobnumber = job.split()[0].strip()
                    # print("Comparing job name: %s,  with path token: %s"%(jobfolder, tok))
                    '''
                    if tok==job:
                        self.set_name( elem='job', name=job )
                        self.set_ID( elem='job', ID=jobs[job] )
                        jobFound=True
                        self.set_dict('asset')
                        self.set_dict('show')
                        break
                    '''
                    if tok==jobfolder :
                        self.set_ID( elem='job', ID=jobsfolders[job] )
                        for jobfullname in jobs:
                            if jobs[jobfullname] == jobsfolders[job]:
                                self.set_name( elem='job', name=jobfullname )
                                
                        jobFound=True
                        self.set_dict('asset')
                        self.set_dict('show')
                        break
            else :
                # Asset or Show+Shot
                # print("DEBUG: Processing tok: %s"%tok)
                #  Prevent Assets that might have the same name as a Shot :
                if tok in ['_DEV', 'ASSETS'] :
                    self.set_tab( _type='ASSET' )
                    continue
                #  Find Asset/Show, once Job is found :
                if not assetFound and not showFound :
                    if not assetFound and self.tab()=='ASSET' :
                        for asset in self.Dict('asset') :
                            if tok==asset['name'] :
                                self.set_name( elem='asset', name=asset['name'] )
                                self.set_ID( elem='asset', ID=asset['ID'] )
                                self.set_tab( _type='ASSET' )
                                assetFound=True
                                self.set_dict('filter')
                                if pub :
                                    self.set_name( elem='filter', name='Published' )
                                else :
                                    self.set_name( elem='filter', name='Work' )
                                self.set_dict('task')
                                self.set_dict('element')
                                break
                    if not assetFound and not showFound and self.tab() !='ASSET' :
                        for show in self.Dict('show') :
                            if tok==show['showname'] :
                                self.set_name( elem='show', name=show['showname'] )
                                self.set_ID( elem='show', ID=show['ID'] )
                                self.set_tab( _type='SHOT' )
                                showFound=True
                                self.set_dict('shot')
                                break
                #  Find Shot, once Show is found :
                if showFound and not taskFound :
                    if not shotFound :
                        for shot in self.Dict('shot') :
                            if tok==shot['name'] :
                                self.set_name( elem='shot', name=shot['name'] )
                                self.set_ID( elem='shot', ID=shot['ID'] )
                                shotFound=True
                                self.set_dict('filter')
                                if pub :
                                    self.set_name( elem='filter', name='Published' )
                                else :
                                    self.set_name( elem='filter', name='Work' )
                                self.set_dict('task')
                                self.set_dict('element')
                                break
                if assetFound or showFound :
                    # We have found the base location of the shot/asset so far
                    #  Find Shot, once Show is found :
                    if not potentialTask and not elementFound and not taskFound:
                        # Element
                        stopelmsearch = False
                        for elm in self.Dict('element'):
                            locs = elm['path'].split('/') if elm['path'].count('/') > 0 else [elm['path']]
                            # print("DEBUG: Compare tok %s with element locs: %s"%(tok, str(locs)))
                            # Process all part of a potential path for the element. Some elements have a path like in/plates
                            # But this support everything, as soon as a part of an element path is detected potentialElement
                            # is set and it will keep tracking the rest of the path to find the element
                            # Needs to stop evaluation of elements
                            for loc in locs:
                                if tok == loc :
                                    if loc == locs[-1]:
                                        # element folder found
                                        # print("DEBUG: Set element: %s"%tok)
                                        # print("DEBUG: Set element name to %s, and ID: %s"%(elm['name'],elm['ID']))
                                        self.set_name( elem='element', name=elm['name'])
                                        self.set_ID( elem='element', ID=elm['ID'])
                                        elementFound     = True
                                        potentialElement = False
                                        stopelmsearch    = True
                                    else:
                                        # print("DEBUG: Set potential element: %s"%tok)
                                        potentialElement = True
                                        stopelmsearch    = True
                                    break
                            if stopelmsearch:
                                break
                        if elementFound:
                            continue
                        pass
                    if not potentialElement and not taskFound :
                        # Task
                        stoptasksearch = False
                        for task in self.Dict('task') :
                            # Tasks names will be matched against full task name, shot task name or folder name.
                            # This is for backwards compatibility with older shows.
                            # The convention is to use the task short name as the task name in the path.
                            # So short task name is need as the task path.
                            locs = task['folder'].split('/') if task['folder'].count('/') > 0 else [task['folder']]
                            # Similar method used before for elements but now with tasks to detect and track any possible task
                            # path. Usually tasks paths looks like tasks/comp
                            # print("DEBUG: Compare tok %s with task locs: %s"%(tok, str(locs)))
                            for loc in locs:
                                if tok == loc :
                                    if loc == locs[-1]:
                                        # Task found
                                        # print("DEBUG: Set task: %s"%tok)
                                        self.set_name( elem='task', name=task['name'] )
                                        self.set_ID( elem='task', ID=task['ID'] )
                                        self.set_taskFolder(task['folder'])
                                        taskFound      =True
                                        potentialTask  = False
                                        stoptasksearch = True
                                        #  Get Basenames :
                                        if taskFound and assetFound==True :
                                            basenames=Api.get_bases( assetID=self.ID( 'asset' ), \
                                                task=self.name( 'task' ).upper() )
                                        elif taskFound and shotFound==True :
                                            # basenames=Api.get_bases( shotID=self.ID( 'shot' ), \
                                                # task=self.name( 'task' ).upper() )
                                            basenames=Api.get_bases( shotID=self.ID( 'shot' ), showID=self.ID( 'show' ),\
                                                task=self.name( 'task' ).upper(), taskID=self.ID('task') )
                                        self.set_dict('base')
                                        break
                                    else:
                                        potentialTask = True
                                        # print("DEBUG: Set potential task: %s"%tok)
                                        break
                            if stoptasksearch:
                                break
                        if taskFound:
                            continue
                        pass
                            # if taskFound or potentialTask:
                                # break
                    elif not basenameFound :
                        for basename in basenames :
                            task_abbrev=F.task_toAbbrev( self.name( 'task' ) )
                            base_abbrev=basename['basename'].replace( '_'+self.name( 'task' )+'_', \
                                '_'+task_abbrev+'_' )
                            # print("DEBUG: Compare tok %s with basename: %s and/or base_abrev: %s"%(tok, basename['basename'], base_abbrev))
                            if tok==basename['basename'] or tok==base_abbrev :
                                self.set_name( elem='base', name=basename['basename'] )
                                self.nim['file']['basename']=basename['basename']
                                basenameFound=True
                                if assetFound==True :
                                    versions=Api.get_vers( assetID=self.ID( 'asset' ), basename=self.name( 'base' ), username=self.userInfo()['name'] )
                                if shotFound==True :
                                    versions=Api.get_vers( shotID=self.ID( 'shot' ), showID=self.ID( 'show' ), basename=self.name( 'base' ), username=self.userInfo()['name'] )
                                self.set_dict('ver')
                                break
                    elif not versionFound :
                        for version in versions :
                            task_abbrev=F.task_toAbbrev( self.name( 'task' ) )
                            ver_abbrev=version['filename'].replace( '_'+self.name( 'task' )+'_', \
                                '_'+task_abbrev+'_' )
                            if tok==version['filename'] or tok==ver_abbrev :
                                # self.set_name( elem='ver', name=version['filename'] )
                                self.set_name( elem='ver', name=version['version'] )
                                self.set_ID( elem='ver', ID=version['fileID'] )
                                self.set_version( version['version'])
                                self.get_nim()['file']['basename'] = version['basename']
                                self.get_nim()['file']['filename'] = version['filename']
                                # Extract user info from file version:
                                self.set_name( elem='user', name=version['username'])
                                self.set_ID( elem='user', ID=version['userID'])
                                versionFound=True
                                break

        # If the path if a file wit a previous version published then we have been able to detect basename and version.
        # Otherwise basename and version haven't been found and we need to guess the from the file path
        # TODO: check if this is actually happening with nuke publishing
        if not basenameFound or not versionFound:
            # Guess basename from file name.
            (basename, tagname, ver) = Api.extract_basename( self, filePath )
            # Fill file key
            self.nim['file']['basename']=basename
            self.nim['file']['filename']=self.name('file')
            self.set_version(str(ver))

        
        #  Derive Server :
        if self.name( 'job' ) :
            # self.set_name( elem='server', name=filePath.split( self.name( 'job' ).split()[0] )[0] )
            server = Api.get_servers( self.ID())[0]
            self.set_server(path=filePath.split( self.name( 'job' ).split()[0] )[0], name=server['server'], Dict=server, ID=server['ID'], _input=None )

        
        #  Derive file extension :
        if F.get_ext( filePath ) :
            self.set_name( elem='fileExt', name=F.get_ext( filePath ) )
            self.set_fileTypeByExt( F.get_ext( filePath ) )


        #  Comp Path :
        pathInfo=""
        if self.tab()=='SHOT' and self.ID('shot') :
            pathInfo=Api.get( {'q': 'getPaths', 'type': 'shot', 'ID' : str(self.ID('shot'))} )
        elif self.tab()=='ASSET' and self.ID('asset') :
            pathInfo=Api.get( {'q': 'getPaths', 'type': 'asset', 'ID' : str(self.ID('asset'))} )
        if not pathInfo :
            P.warning( 'No Path Information found in the NIM API!' )
        else:
            #  Set Comp Path :
            if pathInfo and type(pathInfo)==type(dict()) and 'comps' in pathInfo :
                compPath=os.path.normpath( os.path.join( self.server(), pathInfo['comps'] ) )
                self.set_compPath( compPath=compPath )
            
            #  Set Render Path :
            if pathInfo and type(pathInfo)==type(dict()) and 'renders' in pathInfo :
                renderPath=os.path.normpath( os.path.join( self.server(), pathInfo['renders'] ) )
                self.set_renderPath( renderPath=renderPath )

            #  Set Plates Path :
            if pathInfo and type(pathInfo)==type(dict()) and 'plates' in pathInfo :
                platesPath=os.path.normpath( os.path.join( self.server(), pathInfo['plates'] ) )
                self.set_platesPath( platesPath=platesPath )

            # Shot/Asset path
            if pathInfo and type(pathInfo)==type(dict()) and 'root' in pathInfo :
                shotPath=os.path.normpath( os.path.join( self.server(), pathInfo['root'] ) )
                self.set_shotPath( shotPath=shotPath )

            jobnumber = str(self.name().split()[0])
            jobpath = os.path.normpath(os.path.join(self.server(), jobnumber ))
            self.set_jobPath( jobPath=jobpath )
        
        # DEBUG
        # P.debug( 'Derived the following API information from filepath...' )
        # P.debug( '    %s' % self.Print( debug=True ) )
        # pprint(self.get_nim())

        return self
    
    #  Get Attribute Settings :
    #===------------------------------
    
    def get_elemList(self) :
        'Returns the list of valid GUI elements'
        return self.elements
    
    def get_printElemList(self) :
        'Returns the list of printable GUI element names'
        return self.print_elements
    
    def get_printElem( self, elem='job' ) :
        'Gets the printable name for a given element'
        return self.print_elements[self.elements.index( elem )]
    
    def get_comboBoxes(self) :
        'Returns the list of GUI combo box elements'
        return self.comboBoxes
    
    def get_listViews(self) :
        'Returns the list of GUI list view elements'
        return self.listViews
    
    def get_nim(self) :
        'Returns the current NIM dictionary'
        return self.nim
    
    def userInfo(self) :
        'Gets the user information - user name and ID'
        return self.nim['user']
    
    def server( self, get='' ) :
        'Gets server information'
        if get !='' :
            if get.lower() in ['input'] :
                return self.nim['server']['input']
            elif get.lower() in ['name'] :
                return self.nim['server']['name']
            elif get.lower() in ['path'] :
                return self.nim['server']['path']
            elif get.lower() in ['dict', 'dictionary'] :
                return self.nim['server']['Dict']
            elif get.lower() in ['id'] :
                return self.nim['server']['ID']
        else :
            return self.nim['server']['path']
    
    def Input( self, elem='job' ) :
        'Retrieves the input widget for a given element'
        return self.nim[elem]['input']
    
    def Dict( self, elem='job' ) :
        'Gets the dictionary associated with a given element'
        return self.nim[elem]['Dict']
    
    def name( self, elem='job' ) :
        'Gets the name of the item that an element is set to'
        # if elem == 'job' and self.nim[elem]['name']:
            # Job name is an exception since it is in the form of 'jobnumber jobshortname'. We only care about the first jobnumber.
            # XXX:This can break the UI
            # return self.nim[elem]['name'].split()[0]
        # else:
        return self.nim[elem]['name']
    
    def menuID( self, elem='job' ) :
        'Returns the dictionary of menu IDs.'
        return self.menuIDs[elem]
    
    def ID( self, elem='job' ) :
        'Returns the item ID of the specified element'
        return self.nim[elem]['ID']
    
    def app(self) :
        'Returns the application that NIM is running from'
        return self.nim['app']
    
    def pix( self, elem='asset' ) :
        'Retrieves the pixmap image associated with an element (only assets and shots)'
        img_pix = None
        try:
            img_pix = self.nim[elem]['img_pix']
        except:
            pass
        return img_pix
    
    def label( self, elem='asset' ) :
        'Retrieves the label that a pixmap is assigned to, for a given element (only assets and shots)'
        return self.nim[elem]['img_label']
    
    def tab(self) :
        'Retrieves whether the tab is set to "SHOT", or "ASSET"'
        return self.nim['class']
    
    def pub(self) :
        'Gets the state of the publishing checkbox'
        return self.nim['pub']
    
    def taskFolder(self) :
        'Returns the current task folder.'
        return self.nim['task']['folder']
    
    def mode(self) :
        'Gets the mode of the window'
        return self.nim['mode']
    
    def fileType(self) :
        'Returns the file extension setting'
        return self.nim['fileExt']['fileType']
    
    def filePath(self) :
        'Returns the file path'
        return self.nim['file']['path']
    
    def fileDir(self) :
        'Returns the file directory'
        return self.nim['file']['dir']
    
    def fileName(self) :
        'Returns the file name'
        return self.nim['file']['name']
    
    def version(self) :
        'Returns the file version number'
        return self.nim['file']['version']
    
    def compPath(self) :
        'Returns the comp directory path'
        return self.nim['file']['compPath']
    
    # Added to support new renderPath and platesPath
    def renderPath(self) :
        'Returns the render directory path'
        return self.nim['file']['renderPath']
    
    def platesPath(self) :
        'Returns the plates directory path'
        return self.nim['file']['platesPath']

    # Add job and shot/asset path
    def jobPath(self) :
        'Returns the job root directory path'
        return self.nim['file']['jobPath']
    
    def shotPath(self) :
        'Returns the shot/asset directory path'
        return self.nim['file']['shotPath']

    # Get elements type list
    def get_elementTypes( self ):
        'Returns dictionary with available elements types for publishing'
        return self.nim['elements']
    
    # Get NIM version
    def get_nimVer( self ):
        'Returns NIM version'
        return self.nim['nimver']
    
    #  Set Attributes :
    #===------------------
    
    def set_userInfo( self, userName='', userID='' ) :
        'Sets the User Name and ID'
        self.nim['user']={'name': userName, 'ID': str(userID) }
        return
    
    def set_user( self, userName='' ) :
        'Sets the User Name'
        self.nim['user']['name']=userName
        return
    
    def set_userID( self, userID='' ) :
        'Sets the User ID'
        self.nim['user']['ID']=userID
        return
    
    def set_server( self, _input=None, name=None, path=None, Dict=None, ID=None ) :
        'Sets the server path in NIM'
        if _input !=None :
            self.nim['server']['input']=_input
        if name !=None :
            self.nim['server']['name']=name
        if path !=None :
            self.nim['server']['path']=path
        if Dict !=None :
            self.nim['server']['Dict']=Dict
        if ID !=None :
            self.nim['server']['ID']=ID
        return
    
    def set_input( self, elem='job', widget=None ) :
        'Sets the input widget for a given element'
        self.nim[elem]['input']=widget
        return
    
    def set_baseDict( self, Dict={} ) :
        'Sets the basename dictionary directly.'
        self.nim['base']['Dict']=Dict
        return
    
    def set_dict( self, elem='job', pub=False ) :
        'Sets the dictionary for a given element'
        #print "set_dict: %s" % elem
        dic={}
        
        if elem=='job' :
            #  Only update Job if the dictionary hasn't been set yet :
            if not self.nim[elem]['Dict'] or not len(self.nim[elem]['Dict']) :
                self.nim[elem]['Dict']=Api.get_jobs( userID=self.nim['user']['ID'] )
                if self.nim[elem]['Dict'] == False :
                    P.error("Failed to Set NIM Dictionary")
                    return False
        elif elem=='asset' :
            if self.nim['job']['ID'] :
                self.nim[elem]['Dict']=Api.get_assets( self.nim['job']['ID'] )
        elif elem=='show' :
            if self.nim['job']['ID'] :
                self.nim[elem]['Dict']=Api.get_shows( self.nim['job']['ID'] )
        elif elem=='shot' :
            if self.nim['show']['ID'] :
                self.nim[elem]['Dict']=Api.get_shots( self.nim['show']['ID'] )
        elif elem=='filter' :
            if self.nim['mode'] and self.nim['mode'].lower() in ['load', 'open', 'file'] :
                if self.nim['class']=='SHOT' :
                    if self.nim['shot']['name'] :
                        self.nim[elem]['Dict']=['Published', 'Work']
                elif self.nim['class']=='ASSET' :
                    if self.nim['asset']['name'] :
                        if self.nim['mode'].lower() not in ['file','open'] :
                            self.nim[elem]['Dict']=['Asset Master', 'Published', 'Work']
                        else :
                            self.nim[elem]['Dict']=['Published', 'Work']
            else :
                self.nim[elem]['Dict']=['Work']
        
        elif elem=='element' :
            # New key in teh NIM dictionary. The element key will have a dictionary with all elements and then an element type, ID and path.
            self.nim[elem]['Dict']=Api.get_elementTypes()
            # To extract paths for special elements, plates, renders and comps, shot or asset must be discovered first and set in the NIM dict
            paths = {}
            if self.ID('shot') is not None:
                paths = Api.get_paths( item='shot', ID=int(self.ID('shot')))
            elif self.ID('asset') is not None:
                paths = Api.get_paths( item='asset', ID=int(self.ID('asset')))
            # pprint(paths)
                
            for elm in self.nim[elem]['Dict']:
                if elm['name'] == 'plates':
                    elm['path'] = paths['plates'].replace(paths['root'] + '/', '') if len(paths) is not 0 else ""
                elif elm['name'] == 'renders':
                    elm['path'] = paths['renders'].replace(paths['root'] + '/', '') if len(paths) is not 0 else ""
                elif elm['name'] == 'comps':
                    elm['path'] = paths['comps'].replace(paths['root'] + '/', '') if len(paths) is not 0 else ""
                else:
                    elm['path'] = elm['name']
                        
                    

        elif elem=='task' :
            #REMOVED AS REDUNDANT
            #if self.nim['mode'] and self.nim['mode'].lower() in ['load', 'open', 'file'] :
            
            # WAS INSIDE IF
            if self.nim['filter']['name'] not in ['Select...', 'None', ''] and self.nim['filter']['name'] !='Asset Master' :
                
                #NOT INCLUDING CLASS WHEN LOADING TASKS
                #self.nim[elem]['Dict']=Api.get( {'q': 'getTaskTypes', 'app': self.nim['app'].upper()} )

                #print "Loading %s tasks" % self.nim['class']

                if self.nim['class']=='SHOT' :
                    if self.nim['shot']['name'] not in ['Select...', 'None', ''] :
                        #self.nim[elem]['Dict']=Api.get( {'q': 'getTaskTypes', 'app': self.nim['app'].upper()} )
                        # self.nim[elem]['Dict']=Api.get_tasks(app=self.nim['app'].upper(), shotID=self.nim['shot']['ID'])
                        # Support calls to this function not from an app, from a stand alone command line
                        if self.nim['app'] is not None and len(self.nim['app'])>0:
                            self.nim[elem]['Dict']=Api.get_taskTypes(app=self.nim['app'].upper(), shotID=self.nim['shot']['ID'])
                        else:
                            self.nim[elem]['Dict']=Api.get_taskTypes()
                            # self.nim[elem]['Dict']=Api.get_taskTypes(shotID=self.nim['shot']['ID'])
                            
                elif self.nim['class']=='ASSET' :
                    if self.nim['asset']['name'] not in ['Select...', 'None', ''] :
                        #self.nim[elem]['Dict']=Api.get( {'q': 'getTaskTypes', 'app': self.nim['app'].upper()} )
                        # self.nim[elem]['Dict']=Api.get_tasks(app=self.nim['app'].upper(), assetID=self.nim['asset']['ID'])
                        # Support calls to this function not from an app, from a stand alone command line
                        if self.nim['app'] is not None and len(self.nim['app'])>0:
                            self.nim[elem]['Dict']=Api.get_taskTypes(app=self.nim['app'].upper(), assetID=self.nim['asset']['ID'])
                        else:
                            self.nim[elem]['Dict']=Api.get_taskTypes(assetID=self.nim['asset']['ID'])
                            

            elif self.nim['filter']['name']=='Asset Master' :
                self.nim[elem]['Dict']={}

            # REMOVED AS REDUNDANT
            #else :
            #    if self.nim['class']=='SHOT' :
            #        if self.nim['shot']['name'] not in ['Select...', 'None', ''] :
            #            #self.nim[elem]['Dict']=Api.get( {'q': 'getTaskTypes', 'app': self.nim['app'].upper()} )
            #            self.nim[elem]['Dict']=Api.get_tasks(app=self.nim['app'].upper(), shotID=self.nim['shot']['ID'])
            #    elif self.nim['class']=='ASSET' :
            #        if self.nim['asset']['name'] not in ['Select...', 'None', ''] :
            #            #self.nim[elem]['Dict']=Api.get( {'q': 'getTaskTypes', 'app': self.nim['app'].upper()} )
            #            self.nim[elem]['Dict']=Api.get_tasks(app=self.nim['app'].upper(), assetID=self.nim['asset']['ID'])

        elif elem=='base' :
            bases = None
            if self.nim['filter']['name']=='Published' :
                if self.nim['class']=='SHOT' and self.nim['task']['name'] :
                    bases=Api.get_basesAllPub( shotID=self.nim['shot']['ID'], taskID=self.nim['task']['ID'], username=self.userInfo()['name'] )
                elif self.nim['class']=='ASSET' and self.nim['task']['name'] :
                    bases=Api.get_basesAllPub( assetID=self.nim['asset']['ID'], taskID=self.nim['task']['ID'], username=self.userInfo()['name'] )
            else :
                if self.nim['class']=='SHOT' and self.nim['task']['name'] :
                    bases=Api.get_bases( shotID=self.nim['shot']['ID'], taskID=self.nim['task']['ID'] )
                elif self.nim['class']=='ASSET' and self.nim['task']['name'] :
                    bases=Api.get_bases( assetID=self.nim['asset']['ID'], taskID=self.nim['task']['ID'] )
            if bases:
                self.nim[elem]['Dict']=bases
                
        elif elem=='ver' :
            if self.nim['filter']['name']=='Published' :
                if self.nim['mode'] and self.nim['mode'].lower()=='load' :
                    if self.nim['class']=='SHOT' and self.nim['base']['name'] :
                        self.nim[elem]['Dict']=Api.get_basesPub( shotID=self.nim['shot']['ID'], basename=self.nim['base']['name'], username=self.userInfo()['name'] )
                    elif self.nim['class']=='ASSET' and self.nim['base']['name'] :
                        self.nim[elem]['Dict']=Api.get_basesPub( assetID=self.nim['asset']['ID'], basename=self.nim['base']['name'], username=self.userInfo()['name'] )
                elif self.nim['mode'] and self.nim['mode'].lower() in ['open', 'file'] :
                    if self.nim['class']=='SHOT' and self.nim['base']['name']  :
                        self.nim[elem]['Dict']=Api.get_vers( shotID=self.nim['shot']['ID'], basename=self.nim['base']['name'], pub=True, username=self.userInfo()['name'] )
                    elif self.nim['class']=='ASSET' and self.nim['base']['name'] :
                        self.nim[elem]['Dict']=Api.get_vers( assetID=self.nim['asset']['ID'], basename=self.nim['base']['name'], pub=True, username=self.userInfo()['name'] )
            elif self.nim['filter']['name']=='Asset Master' :
                assetInfo=Api.get_assetInfo( assetID=self.ID('asset') )
                amrPath=os.path.normpath( assetInfo[0]['AMR_path'] )
                fileName=assetInfo[0]['AMR_filename']
                fileDir=os.path.normpath( os.path.join( self.server(get='path'), amrPath ) )
                filePath=os.path.normpath( os.path.join( fileDir, fileName ) )
                self.nim[elem]['Dict']=[{'username': '', 'filepath': fileDir, 'userID': '', 'filename': fileName,
                    'basename': '', 'ext': '', 'version': '', 'date': '', 'note': '', 'serverID': '', 'fileID': ''}]
            else :
                if self.nim['class']=='SHOT' and self.nim['base']['name']  :
                    self.nim[elem]['Dict']=Api.get_vers( shotID=self.nim['shot']['ID'], basename=self.nim['base']['name'], username=self.userInfo()['name'] )
                elif self.nim['class']=='ASSET' and self.nim['base']['name'] :
                    self.nim[elem]['Dict']=Api.get_vers( assetID=self.nim['asset']['ID'], basename=self.nim['base']['name'], username=self.userInfo()['name'] )
        
        return
    
    def set_name( self, elem='job', name=None ) :
        'Sets the name of the selected element item'
        self.nim[elem]['name']=name
        return
    
    def set_menuID( self, elem='job', Dict={} ) :
        ''
        self.menuIDs[elem]=Dict
        return
    
    def set_ID( self, elem='job', ID=None ) :
        'Sets the ID of the selected element item'
        self.nim[elem]['ID']=ID
        return
    
    def set_pic( self, elem='asset', widget=None ) :
        'Sets the pixmap image for a given element (only assets and shots)'
        self.nim[elem]['img_pix']=widget
        return
    
    def set_label( self, elem='asset', widget=None ) :
        'Sets the label, to apply a pixmap image to, for a given element (only assets and shots)'
        self.nim[elem]['img_label']=widget
        return
    
    def set_mode( self, mode='open' ) :
        'Sets the window mode'
        self.nim['mode']=mode
        return
    
    def set_tab( self, _type='SHOT' ) :
        'Sets whether tab is set to "SHOT", or "ASSET"'
        self.nim['class']=_type
        return
    
    def set_pub( self, pub=False ) :
        'Sets the publishing state'
        self.nim['pub']=pub
        return
    
    def set_taskFolder( self, folder='' ) :
        'Sets the Task Folder.'
        self.nim['task']['folder']=folder
        return
    
    def set_mode( self, mode='FILE' ) :
        'Sets the current mode that the window is in'
        self.nim['mode']=mode
        return
    
    def set_filePath(self, filePath=None) :
        '''
        Set file path parts from application or from a given path
        This is a modification to the original NIM function to allow
        settings paths from a given explicit argument.
        The original function only allowed to set the path extracting it from the host
        application. the new filePath argument allows to set file path parts in teh dictionary from a given path.
        This is used in ingest_filePath() to fill the file elements from the given path.

        Parameters
        ----------
        filePath : str, optional
            Optional file path in case we don't want/need to extract file path from a host application, by default None
        '''
        if not filePath:
            self.nim['file']['path']=F.get_filePath()
        else:
            self.nim['file']['path']=filePath
            
        if self.nim['file']['path'] :
            self.nim['file']['name']=ntpath.basename( self.nim['file']['path'] )
            self.nim['file']['dir']=os.path.dirname( self.nim['file']['path'] )
        else :
            self.nim['file']['name']=''
            self.nim['file']['path']=''
        self.nim['file']['basename']=None
    
    def set_fileTypeByExt( self, ext) :
        '''
        Set file type based on file extension

        Parameters
        ----------
        ext : str
            File extension
        '''
        myext = ext[1:] if ext.startswith('.') else ext
        filetype = ""
        if myext == 'hip':
            filetype = 'Houdini Scene'
        elif myext in ('mb', 'ma'):
            filetype = 'Maya Scene'
        elif myext == 'nk':
            filetype = 'Nuke Script'
        elif myext in ('exr', 'jpg', 'jpeg', 'dpx', 'png'):
            filetype = 'Image'
        elif myext in ('mov', 'mp4'):
            filetype = 'Movie'
        elif myext in ('abc'):
            filetype = 'Alembic'
        if filetype:
            self.nim['fileExt']['fileType']=filetype
        else:
            P.warning("File extension not recognized as file type: %s"%ext)            
            
        if filetype:
            self.nim['fileExt']['fileType']=filetype
        return

    def set_fileType( self, fileType='Maya Binary' ) :
        'Sets the current file type the window is set to'
        if fileType in ['Maya Binary', 'Maya Ascii', 'Houdini Scene', 'Nuke Script'] :
            self.nim['fileExt']['fileType']=fileType
        return
    
    def set_version( self, version='' ) :
        'Sets the file version number'
        self.nim['file']['version']=version
        return
    
    def set_compPath( self, compPath='' ) :
        'Sets the comp directory path for the project'
        self.nim['file']['compPath']=compPath
        return

    # Added to support new renderPath and platesPath
    def set_renderPath( self, renderPath='' ) :
        'Sets the render directory path for the project'
        self.nim['file']['renderPath']=renderPath
        return

    def set_platesPath( self, platesPath='' ) :
        'Sets the plates directory path for the project'
        self.nim['file']['platesPath']=platesPath
        return

    # Add set job and show/asset path
    def set_jobPath( self, jobPath='' ) :
        'Sets the job root directory path for the project'
        self.nim['file']['jobPath']=jobPath
        return

    def set_shotPath( self, shotPath='' ) :
        'Sets the shot/asset directory path for the project'
        self.nim['file']['shotPath']=shotPath
        return

    # Get NIM version
    def set_nimVer( self, ver='' ):
        'Set NIM version'
        self.nim['nimver'] = ver
        return
    
    pass # End of class NIM


#  END
