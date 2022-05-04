'''
File:          nim_rohtau_tc.py
Project:       nim
File Created:  Tuesday, 26 April 2022 11:03:02
Author:        Pablo Gimenez (pablo@rohtau.com)
-----
Last Modified: Wednesday, 04 May 2022 12:26:31 CUT
Modified By:   Pablo Gimenez (pablo@rohtau.com)
-----
Copyright 2020 - 2021, rohtau
-----

Time Cards API module
Time cards are a key part of project managing. They are used to track when someone is working and in what is working.
The main information we need to extract from time cards is:
- When a person has been working, mainly to get correct cost projection in NIM
- On what people is working, have an idea of cost both in time and money of a
  particular task
- Being able to get proper cost visualizations, by person, department, shot, etc
  ...

Arquitecture
------------
The first step is logging time cards as json files, we call these Time Cards logging and there is a a set of API functions to deal with this process.
One important aspect that appears in several aeas of the API is the minimum working time on task(MWTT). This is the time we considered enough to start 
tracking a scene into a time card. Is measure in minutes and the default is 10.
- Create log file if it doesn't exists for current task (task used to publish DCC
  scene)
- Update log file if it exists and meet update criteria
  - If there is already a time card closed less than our minimum working time
    then reuse card, otherwise create a new one.
- Cards logs publishing. This basically means creating/updating time card in
  NIM. Again there is a set of API functions for that.
- Cards conform. The idea here is to have tools to get a set of timecards and
  try to make sense of all of them into something tha works inside NIM.
  For instance we can have overlapping cards and NIM simply accumulate all the time wit can end with unrealistic worked hours.
  The idea is at the end of the working day get all the timecards and modify them in order to get a more accurate amount of working time for that day.
'''
#
# Imports
#
import os
import sys
import platform
import tempfile
import getpass
import glob
import json
import random
from datetime   import datetime
from datetime   import timedelta
from random import randrange


# NIM imports
if sys.version_info >= (3,0):
    # from . import nim                as Nim
    from . import nim_api            as nimAPI
    from . import nim_print          as nimP
    # from . import nim_file          as nimF
    from . import nim_rohtau   as nimRt
    # from . import nim_rohtau_utils   as nimUtl
    # from . import nim_win as Win
else:
    # import nim                as Nim
    import nim_api            as nimAPI
    import nim_rohtau   as nimRt
    # import nim_rohtau_utils   as nimUtl
    import nim_print          as nimP
    # import nim_win as Win

#  Variables :
from .import version 
from .import winTitle 
from .import padding 
from .import imgpadding 
from .import mwtt 


#
# Globals
#

#
# Timecards Logging
#
def getTCLogsLoc():
    '''
    Get locations dir for time cards logs.
    Usually:
        /tmp/timecards/$USER
    If location doesn't exists the create it.

    Parameters
    ----------
    

    Returns
    ---------
    str :
        Path to timecards location. If any error happens then False.    

    '''
    # TODO: define a predefined tmp, c:\tmp or /tmp.
    # The problem is that tools like houdini redefine TEMP and returns a path to
    # the Houdini temp, instead of agenera temp.
    # tmpdir = tempfile.gettempdir()
    tmpdir = '/tmp'
    if platform.system() == 'Windows':
        tmpdir = r'C:\tmp'
    # if platform.system() != 'Windows':
        # # In Unix the tmp folder doesnt have a user subfolder.
        # tmpdir += "/%s"%getpass.getuser()
    logsdir = os.path.join(tmpdir, 'timecards', getpass.getuser())
    if not os.path.exists(logsdir):
        try:
            os.makedirs(logsdir, exist_ok=True)
        except FileExistsError as e:
            pass
        # except Exception as e:
            # nimP.error("Can't create temp folder for timecards, Check permission on temp folder: %s"%logsdir, showwindow=True)
            # return False

    return logsdir

def logTC(entity='SHOT', scenepath='', parent='', parentid=0, task='', taskid=0, typeid=0, userid=0, tcid=0, tcpath=''):
    '''
    Main timecards logging function, we always call to this function from any DCC
    Check if the scene is already being racked by a timecard log, tcid and tcpath will have info.
    If not check if there is already a timecard for the task.
    If not, create the log file.
    If it already exists then check close time for the card, if it is less then MWTT then reuse task and update close time.
    If the card is old enough then create a new one.

    Time Card Log Name Convention
    -----------------------------
    A time card log filename looks like:
        PARENT__TASK__TCID.json
    For instance, for a shot named SHL_030, task comp and a timecard id 1234:
        SHL_030__comp__1234.json
    So just extracting the parts of the file name we can know the parent, task and the id of the timecard, this is very handy to
    quickly find potential usable timecards before doing any more complicated processing.

    Parameters
    ----------
    entity : str
        Parent entity: SHOt or ASSET
    scenepath : str
        Path to scene from where we are tracking. Only needed is userid different than current user(Need to create new task)
    parent : str
        Parent name, shot or asset
    parentid : int
        Parent ID
    task : str
        Task type name
    taskid : int
        Task ID for the scene
    typeid : int
        Task type ID
    userid : int
        Current userid.
    tcid : int
        Current Time Card in use id. 0 if there is no Time Card in use for current scene.
    tcpath : str
        Path to current Time Card Log. Empty if there is no Time Card in use for current scene.

    Returns
    ---------
    str
        Path to timecard log file.

    '''
    nimP.info("In logTC")
    # First if a current TC path is provided go straight to update it
    if tcpath:
        if not os.path.exists(tcpath):
            nimP.error("Can't log TC, path to current log file doesn't exists: %s"%tcpath)
            return False
        return updateTCLog(tcpath)

    # Try to find an usable existing TC or create a new one
    logsdir = getTCLogsLoc()
    if not logsdir:
        return False

    # If userid for the log is not the same as our current user then try to find
    # a task for the current user. If there is no task for the current
    # shot/asset, try to create one, if the user refuse then inform no time
    # tracking will take place.
    myuser = nimAPI.get_user()
    myuserid = nimAPI.get_userID()
    if userid != myuserid:
        pubtask = nimRt.pubTask( filepath=scenepath, user=myuser )
        if not pubtask:
            nimP.warning("Time Cards Tracking disable. No task available for user %s->%s"%(parent, task))
            return False
        taskid = int(pubtask['taskID'])
    
    logfiles = glob.glob(logsdir + '/*.json')
    logpath = ''
    tasklogs = []
    tcupdated = False
    tccreated = False
    kwargs = {
        'parent' : parent,
        'parentid' : parentid,
        'task' : task,
        'taskid' : taskid
    }
    for log in logfiles:
        filename = os.path.basename(log)
        filename = os.path.splitext(filename)[0]
        parts    = filename.split('__')
        if parts[0] == parent and parts[1] == task:
            '''
            if int(parts[2]) == tcid:
                # Found time card for current scene, just update end time
                # Call update TC
                logpath = updateTCLog(log)
                if not logpath :
                    return False
                tcupdated = True
                break
            else:
            '''
            # found potential usable timecard log.
            # Call to check time card, it suitable then update, if not then
            # create
            if checkTCLog(log):
                logpath = updateTCLog(log)
                if not logpath:
                    return False
                tcupdated = True
                break
            '''
            else:
                logpath = createTCLog(**kwargs)
                if not logpath:
                    return  False
                tccreated = True
            '''
    if not tcupdated and not tccreated:
        # Need to create new time card
        logpath = createTCLog(**kwargs)
        if not logpath:
            return  False
        tccreated = True


    return logpath

def updateTCLog (logpath):
    '''
    Update given TC log file. 
    Change end time to current time.

    Parameters
    ----------
    logpath : str
        Path to log file.
    

    Returns
    ---------
    str
        Path to the TC log file. False if error
    '''
    nimP.info("In updateTCLog")
    if not os.path.exists(logpath):
        nimP.error("Can't update Time Card log file, doesn't exists: %s"%logpath, showwindow=True)
        return False
    with open(logpath, 'r') as logfile:
        tc = json.load(logfile)
    now = datetime.now()
    isonow = now.isoformat() # Time ISO format: 2022-04-27T11:24:28.317411
    timestamp = isonow.split('.')[0].split('T')[1] # Only get time without microseconds
    tc['end'] = timestamp

    # Write log back.
    with open(logpath, "w") as logfile:
        json.dump(tc, logfile, indent=2)

    # TODO: Publish TC log in NIM (Update Time Card in NIM)

    return logpath

def checkTCLog(logpath):
    '''
    Check if a time card log has been closed (end) before the MWTT has passed.
    If that is the case we can reuse the log, otherwise we will need to create a new one.

    Parameters
    ----------
    logpath : str
        Path to time card log json file

    Returns
    ---------
    bool
        True if we can reuse the card, False otherwise
    '''
    nimP.info("In checkTCLog")
    if not os.path.exists(logpath):
        nimP.error("Can't update Time Card log file, doesn't exists: %s"%logpath, showwindow=True)
        return False
    with open (logpath, 'r') as logfile:
        tc = json.load(logfile)
    now = datetime.now()
    isonow = now.isoformat() # Time ISO format: 2022-04-27T11:24:28.317411
    date,timestamp = isonow.split('.')[0].split('T') # Split date and time

    if tc['date'] != date:
        return False
    # nuke.tprint("Current time: %s"%timestamp)
    # nuke.tprint("End time on card: %s"%tc['end'])
    tcend = datetime.strptime(tc['end'], "%H:%M:%S")
    nowtime = datetime.strptime(timestamp, "%H:%M:%S")
    diff = nowtime - tcend
    # nuke.tprint("Time diff:")
    # nuke.tprint(diff)
    # mwtt is in minutes
    # if diff.seconds//60 > mwtt:
    if diff.seconds//60 > (mwtt*3):
        nimP.info("Old time card found: %s"%os.path.basename(os.path.splitext(logpath)[0]))
        return False # Time card closed later than MWTT

    return True


# Create json file with correct name, at the moment use a random  id for TC,
# later we will implement publishing and do name correctly.
# Set time card id and log path in NIM data for the scene
def createTCLog(parent='', parentid=0, task='', taskid=0, typeid=0, userid=0):
    '''
    Create Log file for a TC and initialise it with th data passed

    Time Card Log format
    --------------------
    Basically is a JSON object with information to publish a time card in NIM
    {
        'id':1234,
        'task':'fx',
        'taskid':34,
        'parent':'SHL_030'
        'parentid': 78,
        'user' : 'pablo',
        'userid' : 7,
        'published' : false
        'date':'2022-05-20',
        'start':'10:00:00',
        'end':'20:00:00'
    }

    Time Card Log Name Convention
    -----------------------------
    A time card log filename looks like:
        PARENT__TASK__TCID.json
    For instance, for a shot named SHL_030, task comp and a timecard id 1234:
        SHL_030__comp__1234.json
    So just extracting the parts of the file name we can know the parent, task and the id of the timecard, this is very handy to
    quickly find potential usable timecards before doing any more complicated processing.

    Parameters
    ----------
    parent : str
        Parent name, shot or asset
    parentid : int
        Parent ID
    task : str
        Task type name
    taskid : int
        Task ID for the scene
    typeid : int
        Task type ID
    userid : int
        Current userid.

    Returns
    ---------
    str
        Path to log file created or False if any error
    '''
    nimP.info("In createTCLog")
    # Check inputs
    if not parent or not parentid or not task or not taskid:
        nimP.error("Any of the mandatory inputs to create a TC log is empty, check Parent, ParentID, Task and TaskID")
        return False

    # Get cur time
    now = datetime.now()
    isonow = now.isoformat() # Time ISO format: 2022-04-27T11:24:28.317411
    date,timestamp = isonow.split('.')[0].split('T') # Split date and time


    tc              = {}
    tc['id']        = 0
    tc['task']      = task
    tc['taskid']    = taskid
    tc['parent']    = parent
    tc['parentid']  = parentid
    tc['user']      = nimAPI.get_user()
    tc['userid']    = nimAPI.get_userID(user=tc['user'])
    tc['published'] = False
    tc['published'] = False
    tc['date']      = date
    tc['start']     = timestamp
    tc['end']       = timestamp

    # Write log .
    logsdir = getTCLogsLoc()
    if not logsdir:
        return False
    rndtcid =  random.randint(0, 9999) # Just temporal, to simulate TC publishing id
    logname = "%s__%s__%d.json"%(parent, task, rndtcid)
    logpath = os.path.join(logsdir, logname)
    with open(logpath, 'w') as logfile:
        json.dump(tc, logfile, indent=2)
    nimP.info("Create TC Log: %s"%logpath)

    # TODO: Publish TC log in NIM (Create Time Card in NIM)

    return logpath



#
# Timecards Logging
#





#
# Timecards Conform
#
