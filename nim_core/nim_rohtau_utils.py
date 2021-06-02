'''
File: nim_rohtau_utils.py
Project: nim_core
File Created: Tuesday, 28 January 2021 12:34:53 pm
Author: Pablo Gimenez (pablo@rohtau.com)
-----
Last Modified: Tuesday, 5th January 2021 12:53:26 am
Modified By: Pablo Gimenez (pablo@rohtau.com>)
-----
Copyright 2020 - 2021, rohtau
-----

Wrapper on top of NIM API
'''

import sys
import platform
import os
import re
# import getpass
import time
# from pathlib import PurePath
from pprint import pprint
from pprint import pformat
from itertools import groupby

if sys.version_info >= (3, 0):
    from . import nim_api as nimAPI
    from . import nim_prefs as nimPrefs
    from . import nim_print as nimP
else:
    import nim_api as nimAPI
    import nim_prefs as nimPrefs
    import nim_print as nimP

#  Variables :
from .import version
from .import winTitle
from .import padding


class shotStatusID:
    '''
    Enum for shot status ID in NIM
    '''
    ON_HOLD = 1
    OMIT = 2
    COMPLETED = 3
    IN_PROGRESS = 4
    APPROVED = 5
    NOT_STARTED = 6
    BLOCKED = 7


class assetStatusID:
    '''
    Enum for asset status ID in NIM
    '''
    ON_HOLD = 1
    OMIT = 2
    COMPLETED = 3
    IN_PROGRESS = 4
    BLOCKED = 5
    REVIEW = 6
    APPROVED = 7


class jobAwardStatusID:
    '''
    Enum for job status ID in NIM
    '''
    BIDDING = 1
    NOT_AWARDED = 2
    AWARDED = 3
    IN_PROGRESS = 4
    COMPLETED = 5
    CLOSED = 6

#
# Utilities
#
def logtimer(msg, start, end=0.0):
    '''
    Write log messages to the terminal using click.echo()
    This is a specialized version of the log() function to output
    timer log messages for profiling

    If end time is not provided, start will be printed as the time.
    If provided the difference between end and start will be the printed time.

    Arguments:
        msg {str} -- log message. A semicolo plus final time will be added.
        start {float} -- start time
        end {float} -- end time
    '''
    print("NIM.Profile ~> %s : %0.4f" %
          (msg, (end-start) if end > 0 else start))

    pass

#
# Jobs
def getjobs():
    """
    Get a dictionary with all jobs and IDs
    { 'JobName' : ID , ... }
    """
    # get NIM jobs
    # XXX: this function is pretty expensive, at the moment in NIM we need to loop through all the users in order
    # to get a full list of jobs
    users = nimAPI.get_userList()
    jobsnames = {}
    for user in users:
        userjobs = nimAPI.get_jobs(user['ID'])
        if userjobs == False:
            continue
        for key in userjobs.keys():
            if key not in jobsnames:
                jobsnames[key.decode('utf-8')] = int(userjobs[key])
    return jobsnames


def getjobIdFromNumber(number):
    """
    Using a job number id string, return it's integer id

    Return -1 if job number(int) is not found
    """
    id = 0
    jobs = getjobs()
    for jobname in jobs.keys():
        names = jobname.split()
        # print("Given number: %s, jobs labels: %s %s"%(number, str(names[0]), str(names[1])))
        if number == names[0].strip() or number == names[1].strip():
            id = int(jobs[jobname])

    return id


def getjobNumberFromId(id):
    """
    Using a job integer id string, return it's job number identifier

    Return empty string job id is not found
    """
    jobinfo = nimAPI.get_jobInfo(id)
    if jobinfo:
        # print (jobinfo)
        return jobinfo[0]['number']

    return ""


def getjobIdNumberTuple(job):
    """
    From and ID or a number return both in a tuple.

    Returns:
        Tuple (ID, number)
        If any error happends ID will -1 and number an empty string
    """
    jobnumber = job
    jobid = -1
    # if isinstance(job, int) or (hasattr(job, 'isnumeric') and job.isnumeric()):
    if isinstance(job, int) or (isinstance(job, str) and job.isdigit()):
        jobnumber = getjobNumberFromId(job)
        jobid = int(job)
        if not jobnumber:
            nimP.error("Can't get job number from given id: %d" % job)
            return (0, "")
    else:
        # jobnumber =  fixjobNumber(job)
        jobid = getjobIdFromNumber(jobnumber)
        if not jobid:
            nimP.error("Can't get job id from given job number: %s" %
                       jobnumber)
            return (0, "")

    return (jobid, jobnumber)


def fixjobNumber(jobnumber):
    """
    Fix jobnumber to follow our convention.
    In some cases we can find some legacy jobnumbers, in order to make this jobs
    working in the pipe we need to fix them and get an usable version.

    This is mainly used to get a proper name for Rez packages.
    Supported fixes:
    - Swap - by _ . Rez packages cant use - in the package name since it is used to split name from version .

    Parameters:
        jobnumber(str): job number identifier

    Returns:
        Job number string fixed
    """
    '''
    last_char_index = jobnumber.rfind("_")
    last_char_sep = jobnumber.rfind("-")
    if last_char_sep > last_char_index:
        # Assume that if there is a - after tha last _, then that is the separator and the jobnumber string is ok
        return jobnumber
    fixedstr = jobnumber[:last_char_index] + "-" + jobnumber[last_char_index+1:]
    '''
    fixedstr = jobnumber.replace('-', '_')

    return fixedstr


def splitJobNumber(jobnumber):
    '''
    Split a job number between job name and job code number
    Jobnumber name convention is: [JOBNAME]_[JOBCODE]: gousto_20001

    Parameters
    ----------
    jobnumber : str
        jobnumber string following convention

    Returns
    -------
    list
        List with job name and job code
    '''
    return jobnumber.rsplit('_', 1)


def getjobLocation(jobid, force_posix=False, noerrors=False):
    """
    For a given jobid get associated server and return mount point path according to host OS.
    Assume jobs have only one server associated

    Parameters:
        jobid(int): internal job id
        force_posix(bool): force posix output even on windows
        noerrors(bool): don't show error

    Return:
        Path to job location given the id.
        This is usually the parent folder for the job, so for a job called test_0001
        which is at /jobs/test_0001 this function will return /jobs
    """
    servers = nimAPI.get_jobServers(jobid)
    jobnumber = getjobNumberFromId(jobid)
    # print(servers)
    if not servers:
        if not noerrors:
            nimP.error(
                "Can't get server from given job id number or name: %s" % jobid)
        return ""
    path = servers[0]['path']
    winpath = servers[0]['winPath'].replace('/', '\\')
    macpath = servers[0]['winPath']

    jobpath = path
    # Add job number
    if not force_posix and platform.system() == 'Windows':
        jobpath = winpath
        jobpath = os.path.join(jobpath, jobnumber)
    else:
        jobpath += "/" + jobnumber
    # jobpath = os.path.join( jobpath, jobnumber )

    return jobpath


def isJobOnline(jobid):
    '''
    Check if a job is online

    Parameters
    ----------
    jobid : int
        Job ID

    Returns
    -------
    bool
        True or False depending if the job is online
    '''
    if len(getjobLocation(jobid, noerrors=True)):
        return True
    else:
        return False

    pass


#
# Shows
def getshowIdFromName(jobid, showname):
    """
    From a show name returns it's ID

    Paremeters:
        jobid(int): Id for working job
        showname(str): name of a show in the selected job.

    Returns:
        show ID(int). Return 0 is show is not found
    """
    shows = nimAPI.get_shows(jobid)
    if not shows:
        nimP.error("Can't get shows from given job id number or name: %s" % jobid)
        return None

    for show in shows:
        if show['showname'] == showname:
            return int(show['ID'])

    return 0


def getshowsIDDict(jobid):
    '''
    Create a dictionary with ID as keys and show name as value
    Ideal to search shows names by ID.

    Arguments:
        jobid {int} -- Job id to search

    Returns:
        dict -- Dictionary in the form {ID(int) : NAME(str)}
    '''
    shows = nimAPI.get_shows(jobid)
    if not shows:
        nimP.error("Can't get shows from given job id number or name: %s" % jobid)
        return None

    showsid = {}
    for show in shows:
        showsid[int(show['ID'])] = show['showname']
    return showsid


#
# Shots
def getshots(jobid, showid=None):
    """
    Return all shots for a given job.
    Optionally also filter by a show id/name

    The result is a dictionary with the id of the show and
    as value a list of all shots objects

    If any errors happens return None
    """

    shots = {}
    shows = nimAPI.get_shows(jobid)
    if not shows:
        nimP.error("Can't get shows from given job id number or name: %s" % jobid)
        return None

    for show in shows:
        if showid is not None:
            if showid != int(show['ID']) and showid != show['showname']:
                continue
        shots[show['ID']] = nimAPI.get_shots(show['ID'])

    return shots


def getshotIdFromName(jobid, shotname):
    """
    From a shot name returns it's ID

    Paremeters:
        jobid(int): Id for working job
        shotname(str): name of a shot in the selected job.

    Returns:
        shot ID(int). Return -1 is shot is not found
    """
    shots = getshots(jobid)
    if shots is None:
        nimP.error("Can't get shots from given job id: %s" % jobid)
        sys.exit()
    for showid in shots:
        for shot in shots[showid]:
            # print(shot)
            if shot['name'] == shotname:
                return int(shot['ID'])
    return 0

    pass


def getshotsIDDict(jobid, showid=None):
    '''
    Create a dictionary with ID as keys and shot name as value
    Ideal to search shots names by ID.
    It can optionally be filtered by show

    Arguments:
        jobid {int} -- Job id to search

    Keyword Arguments:
        showid {int} -- Show to filter shots (default: {None})

    Returns:
        dict -- Dictionary in the form {ID(int) : NAME(str)}
    '''
    shots = getshots(jobid, showid)
    if shots is None:
        return None
    shotsid = {}
    for show in shots:
        for shot in shots[show]:
            shotsid[int(shot['ID'])] = shot['name']
    return shotsid

#
# Assets
def getassetIdFromName(jobid, assetname):
    """
    From a shot name returns it's ID

    Asset Name:
        Asset name is expected to follow the convention: cat/name
        It should look something like:
            character/crag
            vehicle/car/mercedesSLK

    Paremeters:
        jobid(int): Id for working job
        assetname(str): name of a shot in the selected job.

    Returns:
        Asset ID(int). Return 0 if asset is not found
    """
    assets = nimAPI.get_assets(jobid)
    (cat, name) = os.path.split(assetname)
    for asset in assets:
        assetcat = getassetcategory(asset['ID'])
        if cat == assetcat and name == asset['name']:
            return int(asset['ID'])

    return 0

    print(asset)


def getassetsIDDict(jobid):
    '''
    Create a dictionary with ID as keys and asset name as value
    Ideal to search assets names by ID.

    Arguments:
        jobid {int} -- Job id to search


    Returns:
        dict -- Dictionary in the form {ID(int) : NAME(str)}
    '''
    assets = nimAPI.get_assets(jobid)
    if assets is None:
        nimP.error(
            "Can't get assets from given job id number or name: %s" % jobid)
        return None
    assetsid = {}
    for asset in assets:
        assetsid[int(asset['ID'])] = asset['name']
    return assetsid


def getassetcategory(assetid):
    """
    Given an asset id, return it's category

    If assets doesn't exists then return None
    """
    assetinfo = nimAPI.get_assetInfo(assetid)[0]
    if not assetinfo:
        return None
    if 'customKeys' not in assetinfo:
        return None
    for key in assetinfo['customKeys']:
        if key['keyName'] == 'Category':
            if 'dropdownOptions' in key:
                return key['dropdownText']
            else:
                return key['value']

    return ""


def getassetPkgName(assetid, assetname="", cat=""):
    """
    Given an asset id, return it's package full name.
    A package full name is the category path plus the asset name,
    with / replaced by _ .

    Parameters:
        assetid(int): asset ID in case the asset name is not passed.
        assetname(str): name of the asset, if not passed then assetid is used to retrieve from NIM
        cat(str): asset category. If not passed will be retrieved from NIM using assetid

    Example:
        character/crag -> character_crag
        vehicle/car/mercedesSLK -> vehicle_car_mercedesSLK

    If assets doesn't exists then return empty string
    """
    if not assetname:
        assetinfo = nimAPI.get_assetInfo(assetid)[0]
        if not assetinfo:
            return ""
        assetname = assetinfo['assetName']
    if not cat:
        cat = getassetcategory(assetid)
        if not cat:
            return ""
    return cat.replace('/', '_') + '_' + assetname

#
# Tasks
def gettasksTypesIDDict():
    '''
    Create a dictionary with ID as keys and task types names as value
    Ideal to search tasks types names by ID.

    Returns:
        dict -- Dictionary in the form {ID(int) : NAME(str)}
    '''
    tasks = nimAPI.get_taskTypes()

    if tasks is None:
        nimP.error(
            "Can't get tasks types from given job id number or name: %s" % jobid)
        return None
    tasksid = {}
    for task in tasks:
        tasksid[int(task['ID'])] = task['name']
    return tasksid


def gettasksIDDict(jobid):
    '''
    Create a dictionary with ID as keys and task name as value
    Ideal to search tasks names by ID.

    Arguments:
        jobid {int} -- Job id to search


    Returns:
        dict -- Dictionary in the form {ID(int) : NAME(str)}
    '''
    tasks = nimAPI.get_tasks(jobid)

    if tasks is None:
        nimP.error("Can't get tasks from given job id number or name: %s" % jobid)
        return None
    tasksid = {}
    for task in tasks:
        tasksid[int(task['ID'])] = task['name']
    return tasksid


def gettaskTypesIdFromName(taskname):
    """
    From a task name returns it's ID

    Paremeters:
        taskname(str): name of a task to get it's ID

    Returns:
        task ID(int), 0 if not found
    """
    tasks = nimAPI.get_taskTypes()
    # print("Tasks:")
    # print(tasks)
    for task in tasks:
        if task['name'] == taskname:
            # print("Found task woth ID: %d"%int(task['ID']))
            return int(task['ID'])

    return 0


def getcustomTaskInfo(ID=None, itemClass=None, itemID=None):
    '''
    Use custom rohtau API from NIm Labs to get all tasks from a parent: job, show, shot or asset
    Or get all the details from a task given it's ID

    The main difference between this custom function and the default nimAPU.getTaskInfo()  is this
    one accept as parent, itemClass, shows and job IDs, this mean we don't need to loop through all shots
    or asset to get all tasks for a job or show, we can do it in one single query which much efficient.

    Parameters
    ----------
    ID : str, optional
        Task ID, by default None
    itemClass : str, optional
        Task parent: job, show, shot or asset, by default None
    itemID : [type], optional
        Parent Id, by default None

    Returns
    -------
    dict
        Task dictionary
    '''

    params = {'q': 'getTaskInfo'}
    if ID is not None:
        params['ID'] = ID
    if itemClass is not None:
        params['class'] = itemClass
    if itemID is not None:
        params['itemID'] = itemID

    nim_url = nimPrefs.get_url()
    custom_nim_url = nim_url.replace('nimAPI.php', '_custom/rohtauAPI.php')
    custom_nim_url += '?'
    # print("NIM Url: %s"%custom_nim_url)
    # result = nimAPI.connect( method='get', params=params, nimURL='http://localhost:8888/_client/rohtau/rohtauAPI.php?' )
    result = nimAPI.connect(method='get', params=params, nimURL=custom_nim_url)
    return result


def getuserTask(userid, tasktype, parent, parentID):
    '''
    Search for a task for an user in a shot or asset

    Parameters
    ----------
    userid : int
        User id to search a task for
    tasktype: int
        Task type name or ID
    parent : str
        task parent: shot or asset
    parentID : int
        Parent ID

    Returns
    -------
    dict
        task dictionary or False if error or task not found
    '''
    tasktypeID = tasktype
    if isinstance(tasktype, str) and tasktype.isdigit():
        tasktypeID = int(tasktype)
    elif isinstance(tasktype, str):
        tasktypeID = gettaskTypesIdFromName(tasktype)
    if not tasktypeID:
        nimP.error("Task type name or ID not found")
        return False

    tasks = nimAPI.get_taskInfo(itemClass=parent.lower(), itemID=parentID)
    # import nuke
    # nuke.tprint("Tasks:")
    # nuke.tprint(pformat(tasks))
    # nuke.tprint("Look for task type ID: %d for userID: %d"%(tasktypeID, userid))
    # print("Tasks:")
    # print(pformat(tasks))
    # print("Look for task type ID: %d for userID: %d"%(tasktypeID, userid))
    for task in tasks:
        if int(task['typeID']) == tasktypeID and int(task['userID']) == userid:
            return task

    return False

def createTaskFromFilepath(path, user):
    '''
    Search for a task for an user in a shot or asset

    Parameters
    ----------
    path : str
        Path t oscene to get task from
    user : str
        User name to create the task for

    Returns
    -------
    bool
        True if task for user already exists or has been created. False if creation failed
    '''
    print("Create task from %s for %s"%(path, user))


#
# Elements
def getelementsIDDict():
    '''
    Create a dictionary with ID as keys and element name as value
    Ideal to search elements names by ID.

    Returns:
        dict -- Dictionary in the form {ID(int) : NAME(str)}
    '''
    elements = nimAPI.get_elementTypes()
    elementsid = {}

    if elements is None:
        nimP.error(
            "Can't get elements from given job id number or name: %s" % jobid)
        return None
    for element in elements:
        elementsid[int(element['ID'])] = element['name']
    return elementsid


def getelementID(element):
    '''
    Get element ID from name

    Returns:
        int -- element name or -1 if it doesn't exist
    '''
    elements = nimAPI.get_elementTypes()
    # print("Elements Types:")
    # print(elements)
    if elements is None:
        nimP.error("Can't get elements types")
        return None
    for elm in elements:
        if elm['name'] == element:
            return int(elm['ID'])
    return -1


def getcustomFindElements(name=None, path=None, jobID=None, showID=None, shotID=None, assetID=None, taskID=None, renderID=None, elementTypeID=None, ext=None, metadata=None):
    '''
    Use custom rohtau API from NIm Labs to get all elements from a list of tasks.

    The main difference with nimAPI_find_elements is that this one accept a comma separated list of
    tasks IDs in order to get all elements for a list of tasks in one query, making the process much efficient than
    querying for every task separately.

    Parameters
    ----------
    name : str, optional
        Filter by this name, by default None
    path : str, optional
        Filter by path, by default None
    jobID : str, optional
        Get elements parented to this job, by default None
    showID : str, optional
        Get elements parented to this show, by default None
    shotID : str, optional
        Get elements parented to this shot, by default None
    assetID : str, optional
        Get elements parented to this asset, by default None
    taskID : str, optional
        Get elements parented to this task or comma separeted list of tasks, by default None
    renderID : str, optional
        Elements parented to a render review, by default None
    elementTypeID : str, optional
        Elements of this elements type, by default None
    ext : str, optional
        Elements with this extension, by default None
    metadata : str, optional
        Filter by metadata, by default None

    Returns
    -------
    dict
        Task dictionary
    '''
    params = {'q': 'findElements'}

    if name is not None:
        params['name'] = name
    if path is not None:
        params['path'] = path
    if jobID is not None:
        params['jobID'] = jobID
    if showID is not None:
        params['showID'] = showID
    if shotID is not None:
        params['shotID'] = shotID
    if assetID is not None:
        params['assetID'] = assetID
    if taskID is not None:
        params['taskID'] = taskID
    if renderID is not None:
        params['renderID'] = renderID
    if elementTypeID is not None:
        params['elementTypeID'] = elementTypeID
    if ext is not None:
        params['ext'] = ext
    if metadata is not None:
        params['metadata'] = metadata

    nim_url = nimPrefs.get_url()
    custom_nim_url = nim_url.replace('nimAPI.php', '_custom/rohtauAPI.php')
    custom_nim_url += '?'
    # print("NIM Url: %s"%custom_nim_url)
    # result = nimAPI.connect( method='get', params=params, nimURL='http://localhost:8888/_client/rohtau/rohtauAPI.php?' )
    result = nimAPI.connect(method='get', params=params, nimURL=custom_nim_url)
    return result


def findElements(jobid, name="", shotid=0, assetid=0, taskid=0, elementid=0, userid=0, plain=False, profile=False):
    '''
    Get a list of published elements for job, shot or asset.
    Filtered by task, type, user and name.

    Arguments:
        jobid {str} -- Job ID

    Keyword Arguments:
        name{str} --  name to filter search. Name will search the passed string in elements names.
        shotid {int} -- Shot ID for filtering (default: {""})
        assetid {int} -- Asset ID for filtering (default: {""})
        taskid {int} -- Task Type ID(default: {""})
        elementid {int} -- Element Type ID for filter(default: {""})
        userid {int} -- User ID for filtering.(default: {""})
        plain {bool} -- Just list results without formatting (default: {False})

    Returns:
        list -- List of elements, or empty list if search didn't find anything.
    '''

    # isshot    = len(shotid) > 0
    # isasset   = len(assetid) > 0
    # istask    = len(taskid) > 0
    # iselement = len(elementid) > 0
    # elementid = 0
    # userid    = 0

    if profile:
        taskstime = 0.0
        filestime = 0.0
        tstart = 0.0
    # print("find_elements arguments: Job: %s, ShotID=%s, AssetId=%s, TaskID=%s, Type=%s, User=%s, Name=%s, Plain=%d"%( job, shotid, assetid, taskid, typeid, user, name, plain))

    # print("JobID= %d"%jobid)
    elmts = []
    taskelmts = None
    typeelmts = None
    tasks = []
    if shotid or assetid:
        # filter tasks by shot or asset
        if profile:
            tstart = time.perf_counter()

        tasks = nimAPI.get_taskInfo(itemClass='shot', itemID=shotid) if shotid else nimAPI.get_taskInfo(
            itemClass='asset', itemID=assetid)

        if profile:
            taskstime += time.perf_counter() - tstart
    else:
        # return all tasks for all shots and assets
        if profile:
            tstart = time.perf_counter()

        # Custom API:
        tasks = getcustomTaskInfo(itemClass='job', itemID=jobid)
        # print("Number of tasks: %d"%len(tasks))
        # pprint(tasks, indent=4)

        if profile:
            taskstime += time.perf_counter() - tstart

    # Filter by task
    if taskid:
        tasks = [task for task in tasks if int(task['typeID']) == taskid]
    # Filter by user
    if userid:
        tasks = [task for task in tasks if int(task['userID']) == userid]
    # print("Filtered tasks")
    # print(tasks)

    # Using new custom API
    if profile:
        tstart = time.perf_counter()
    tasksstr = tasks[0]['taskID']
    tasksidsdict = {}
    tasksidsdict[tasks[0]['taskID']] = 0
    if len(tasks) > 1:
        for idx in range(1, len(tasks)):
            tasksstr += ",%s" % tasks[idx]['taskID']
            tasksidsdict[tasks[idx]['taskID']] = idx
    # print(tasksstr)
    if elementid:
        elmts = getcustomFindElements(taskID=tasksstr, elementTypeID=elementid)
    else:
        elmts = getcustomFindElements(taskID=tasksstr)
    if profile:
        filestime += time.perf_counter() - tstart

    if not plain:
        if elmts is not None and len(elmts) > 0:
            # Try to fill as much data as possible from the task info
            for elmt in elmts:
                elmt['shotID'] = tasks[tasksidsdict[elmt['taskID']]
                                       ]['shotID'] if elmt['shotID'] is None else elmt['shotID']
                elmt['assetID'] = tasks[tasksidsdict[elmt['taskID']]
                                        ]['assetID'] if elmt['assetID'] is None else elmt['assetID']
                elmt['userID'] = tasks[tasksidsdict[elmt['taskID']]
                                       ]['userID'] if elmt['userID'] is None else elmt['userID']
                if elmt['datetime'] is None and tasks[tasksidsdict[elmt['taskID']]]['start_date'] is not None:
                    elmt['datetime'] = tasks[tasksidsdict[elmt['taskID']]
                                             ]['start_date']
                elmt['typeID'] = tasks[tasksidsdict[elmt['taskID']]]['typeID']

    # Filter by passed entity name, as an ID or a name string to search
    if name is not None and len(name) > 0:
        if name.isnumeric():
            # filter by element id
            elmts = [elm for elm in elmts if elm['ID'] == name]
        else:
            # filter by name
            elmts = [elm for elm in elmts if re.search(
                name, elm['name']) is not None]

    if profile:
        logtimer("Tasks lookup", taskstime)
        logtimer("Files lookup", filestime)

    if elmts is None or not len(elmts):
        return []

    return elmts

#
# Files
def find_basenames(showid=None, shotid=None, assetid=None):
    files = []

    if showid:
        files.extend(nimAPI.find_files(parent='show', parentID=showid))
    elif shotid:
        files.extend(nimAPI.find_files(parent='shot', parentID=shotid))
    elif assetid:
        files.extend(nimAPI.find_files(parent='asset', parentID=assetid))

    files.sort(key=lambda content: content['basename'])
    grouped_files = groupby(files, lambda content: content['basename'])

    basename_groups = {}

    for basename, file in grouped_files:
        basename_files = []
        for fileInfo in file:
            basename_files.append(fileInfo)
        basename_groups[basename] = basename_files

    return basename_groups


def findFiles(jobid, name="", showid=0, shotid=0, assetid=0, taskid=0, elementid=0, userid=0, published=False, last=False, profile=False):
    '''
    Get a list of published files basenames for show, shot or asset.
    Filtered by task, type, user and name.

    Arguments:

    Keyword Arguments:
        jobid {str}     : Job ID
        name {str}      : name to filter search. Name will search the passed string in elements names.
        showid {int}    : Show/Seq ID for filtering. Can be a list as well (default: {""})
        shotid {int}    : Shot ID for filtering. Can be a list as well  (default: {""})
        assetid {int}   : Asset ID for filtering. Can be a list as well  (default: {""})
        taskid {int}    : Task Type ID(default: {""})
        elementid {int} : Element Type ID for filter(default: {""})
        userid {int}    : User ID for filtering.(default: {""})
        last {bool}     : Just list results for last version (default: {False})
        mine {bool}     : Just list results for files owned by caller (default: {False})

    Returns:
        dict -- Dict where  keys are basenames and values are list of dicts for every version.
    '''

    # isshot    = False
    # isasset   = False
    # istask    = False
    # iselement = False
    # elementid = 0
    # userid    = 0

    # print("findFiles arguments: Job: %d, ShowID=%d, ShotID=%d, AssetId=%d, TaskID=%d, Element=%d, UserID=%d, Entity=%s, Last=%d"%( jobid, showid, shotid, assetid, taskid, elementid, userid, name, last))

    # print("JobID= %d"%jobid)
    files     = []
    taskelmts = None
    typeelmts = None
    tasks     = []
    showsid   = []
    shotsid   = []
    assetsid  = []
    doshows   = False
    doshots   = False
    doassets  = False
    basenames = {}
    basenametime = 0.0
    verstime = 0.0
    versinfotime = 0.0
    tstart = 0.0

    if taskid:
        tasks.append(taskid)

    # Process filters
    if not showid and not shotid and not assetid:
        showsid = getshowsIDDict( jobid ).keys()
        for show in showsid:
            shotsid.extend(getshotsIDDict(jobid, show).keys())
        assetsid = getassetsIDDict(jobid).keys()
    elif showid:
        if isinstance(showid, (list, tuple)):
            showsid = showid
        else:
            showsid = [showid]
        for show in showsid:
            shotsid.extend(getshotsIDDict(show).keys())
    elif shotid:
        if isinstance(shotid, (list, tuple)):
            shotsid = shotid
        else:
            shotsid = [shotid]
    elif assetid:
        if isinstance(assetid, (list, tuple)):
            assetsid = assetid
        else:
            assetsid = [assetid]


    if profile:
        tstart = time.perf_counter()
    for show in showsid:
        basenames.update(find_basenames(showid=show))
    for shot in shotsid:
        basenames.update(find_basenames(shotid=shot))
    for asset in assetsid:
        basenames.update(find_basenames(assetid=asset))
    if profile:
        basenametime += time.perf_counter() - tstart
        
        
    if profile:
        tstart = time.perf_counter()
    if tasks:
        basenames = {key: value for ( key, value ) in basenames.items() if int(basenames[key][0]['task_type_ID']) in tasks}
    if elementid:
        basenames = {key: value for ( key, value ) in basenames.items() if basenames[key][0]['customKeys']['Element Type'] == str(elementid)}
    if name:
        basenames = {key: value for ( key, value ) in basenames.items() if re.search(name, key) is not None}
        
    if userid or published:
        for basename in basenames:
            if userid:
                basenames[basename] = [version for version in basenames[basename] if int(version['userID']) == userid]
            if published:
                basenames[basename] = [version for version in basenames[basename] if int(version['isPublished'])]
    if last:
        basenames = {key: [value[0]] for ( key, value ) in basenames.items() }
    if profile:
        verstime += time.perf_counter() - tstart
        
    # pprint(basenames)


    if profile:
        logtimer("Basenames lookup", basenametime)
        logtimer("Versions lookup", verstime)
        # logtimer("Versions Info lookup", versinfotime)

    return basenames


def splitName(filename, error=True):
    '''
    Split a filename according with the name convention:
        [SHOT|ASSET]__[TASK[_ELEMTYPE]]__[TAG]__[VER]
        [SHOT|ASSET]__[TASK]__[TAG]__[VER]

    The return is a dict with:
    - base: Basename [SHOT|ASSET]__[TASK[_ELEMTYPE]]__[TAG]
    - shot: Shot|Asset name
    - task : Task name
    - elem: Elem Type (Not Mandatory, not used by scene files)
    - tag: Tag (Not Mandatory, name is not mandatory, specially for scene files)
    - ver: Ver as an integer number


    Parameters
    ----------
    filename : str
        filename following name convention
    error :  bool
        whether or not report error if name convention wrong. If not report warning

    Returns
    -------
    dict
        Dict with keys: {'base', 'shot', 'task', 'elem', 'tag', 'ver'}
    '''
    fileparts = {'base':'', 'shot':'', 'task':'', 'elem':'','tag':'','ver':0}
    filenoext = filename.split('.')[0]
    basenameparts = filenoext.split('__')
    if len(basenameparts) < 3:
        if error:
            nimP.error("Filename not following name convention. Not enough fields: %s" % filename)
        else:
            nimP.warning("Filename not following name convention. Not enough fields: %s" % filename)
        return False
    fileparts['base'] = '__'.join(basenameparts[:-1])  # Exclude ver part
    ver = basenameparts[-1][1:]  # Get ver part and remove the initial v
    if not ver.isdigit():
        if error:
            nimP.error("Filename not following name convention. Wrong version string. Only number allowed after v: %s" % filename)
        else:
            nimP.warning("Filename not following name convention. Wrong version string. Only number allowed after v: %s" % filename)
        return False
    fileparts['ver']  = int(ver)
    fileparts['shot'] = basenameparts[0]
    task              = basenameparts[1]
    fileparts['task'] = task.split('_')[0] if task.count('_') else task
    fileparts['elem'] = task.split('_')[1] if task.count('_') else "" # elem is not mandatory
    fileparts['tag']  = basenameparts[2] if len(basenameparts) > 3 else "" # tag is not mandatory

    return fileparts

#
# Users
def getuserID(username):
    '''
    Get user ID from name

    Returns:
        int -- user name or -1 if it doesn't exist
    '''
    users = nimAPI.get_userList()
    if users is None:
        nimP.error("Can't get users list")
        return None
    # pdprint(users)
    # Add default domain
    usernamedomain = username + "@rohtau.com"
    for user in users:
        if user['username'] == username or user['username'] == usernamedomain:
            return int(user['ID'])
    return -1

def getuserName(userid):
    '''
    Get user name from ID

    Returns
    -------
    int
        user name or False if it doesn't exist
    '''
    users = nimAPI.get_userList()
    if users is None:
        nimP.error("Can't get users list")
        return None
    # pprint(users)
    # Add default domain
    for user in users:
        if int(user['ID']) == userid:
            return user['username']
    return False


def getusersIDDict():
    '''
    Create a dictionary with ID as keys and user name as value
    Ideal to search users by ID.

    Returns:
        dict -- Dictionary in the form {ID(int) : NAME(str)}
    '''
    users = nimAPI.get_userList()
    usersid = {}

    if users is None:
        nimP.error("Can't get users")
        return None
    for user in users:
        usersid[int(user['ID'])] = user['username']
    return usersid

#
# Templates for Rez packages


def updateJobTemplateData(job, template):
    """
    Get a template string, output from reading a template file and update it
    with job information from NIM using tags in the template

    Parameters:
        job(int): job ID or job number
        template: string with contents of the template file

    Returns:
        template string ready to be writing into destination file with data updated from NIM
        False if an error happens
    """
    (jobid, jobnumber) = getjobIdNumberTuple(job)
    if not jobid:
        return False
    jobinfo = nimAPI.get_jobInfo(jobid)
    # print(jobinfo)
    jobpath = getjobLocation(jobid, force_posix=True)
    if not os.path.exists(jobpath):
        nimP.error(
            "Job location is not accessible, is the job online?: %s" % jobpath)
        return False

    res = template.replace('<name>', fixjobNumber(jobnumber))
    res = res.replace('<number>', jobnumber)
    res = res.replace('<path>', jobpath)

    return res


def updateShotTemplateData(job, shotid, template):
    """
    Get a template string, output from reading a template file and update it
    with job information from NIM using tags in the template

    Parameters:
        jobid(int): job ID or job number
        template: string with contents of the template file

    Returns:
        template string ready to be writing into destination file with data updated from NIM
        False if an error happens
    """
    (jobid, jobnumber) = getjobIdNumberTuple(job)
    if not jobid:
        return False
    jobinfo = nimAPI.get_jobInfo(jobid)[0]
    jobloc = os.path.dirname(getjobLocation(jobid, force_posix=True))
    shotinfo = nimAPI.get_shotInfo(shotid)[0]
    shotpaths = nimAPI.get_paths('shot', shotid)
    shotpath = shotpaths['root']
    shotplatespath = shotpaths['plates']
    shotcompspath = shotpaths['comps']
    shotrenderspath = shotpaths['renders']
    shotpath = jobloc + '/' + shotpath
    shotplatespath = jobloc + '/' + shotplatespath
    shotcompspath = jobloc + '/' + shotcompspath
    shotrenderspath = jobloc + '/' + shotrenderspath
    # print( nimAPI.get_paths( 'shot', shotid ))

    res = template.replace('<name>', shotinfo['shotName'])
    res = res.replace('<path>', shotpath)
    res = res.replace('<job>', fixjobNumber(jobinfo['number']))
    res = res.replace('<plates>', shotplatespath)
    res = res.replace('<comps>', shotcompspath)
    res = res.replace('<renders>', shotrenderspath)

    return res


def updateAssetTemplateData(job, assetid, template):
    """
    Get a template string, output from reading a template file and update it
    with job information from NIM using tags in the template

    Parameters:
        jobid(int): job ID or job number
        template: string with contents of the template file

    Returns:
        template string ready to be writing into destination file with data updated from NIM
        False if an error happens
    """
    (jobid, jobnumber) = getjobIdNumberTuple(job)
    if not jobid:
        return False
    jobinfo = nimAPI.get_jobInfo(jobid)[0]
    jobloc = os.path.dirname(getjobLocation(jobid, force_posix=True))
    assetinfo = nimAPI.get_assetInfo(assetid)[0]
    cat = getassetcategory(assetid)
    # print(nimAPI.get_paths( 'asset', assetid ))
    assetpaths = nimAPI.get_paths('asset', assetid)
    assetpath = assetpaths['root']
    assetcompspath = assetpaths['comps']
    assetrenderspath = assetpaths['renders']
    assetpath = jobloc + '/' + assetpath
    assetcompspath = jobloc + '/' + assetcompspath
    assetrenderspath = jobloc + '/' + assetrenderspath
    # assetname        = cat + '_' + assetinfo['assetName']
    assetname = getassetPkgName(
        assetid, assetname=assetinfo['assetName'], cat=cat)
    assetnamepath = assetname.replace('_', '/')

    res = template.replace('<name>', assetname)
    res = res.replace('<path>', assetpath)
    res = res.replace('<assetpath>', assetnamepath)
    res = res.replace('<job>', fixjobNumber(jobinfo['number']))
    res = res.replace('<comps>', assetcompspath)
    res = res.replace('<renders>', assetrenderspath)

    return res


def getEntitiesList(type='show', pattern="all"):
    """
    Get a list of elements depending on the type to look for and a pattern.
    Type can be:
    - show (sequences, episodes)
    - shots
    - assets

    Pattern is a comma separated list of names or glob patterns:
    GIS_001,GIS_002,GIS_003
    TWS_00*,G*

    The spacial pattern "all" will match all elements for given type,
    all sequences, all shots or all assets .

    Keyword Arguments:
        type {str} -- type of entity to look for (default: {'show'})
        pattern {str} -- pattern for look up (default: {"all"})

    Returns:
        tuple -- tuple with ordered list of entities and entities dictionary with publish info and path
    """

    # TODO: make function in nim_rohtau_utils to get a list of shots or assets based on a pattern

    # return ( elements, elementsdict)
    pass
