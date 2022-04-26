'''
File:          nim_rohtau_tc.py
Project:       nim
File Created:  Tuesday, 26 April 2022 11:03:02
Author:        Pablo Gimenez (pablo@rohtau.com)
-----
Last Modified: Tuesday, 02 November 2021 01:28:36 CUT
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
import platform
import tempfile
import getpass
import glob
import json
from datetime   import datetime
from datetime   import timedelta


# NIM imports
if sys.version_info >= (3,0):
    # from . import nim                as Nim
    # from . import nim_api            as nimAPI
    from . import nim_print          as nimP
    # from . import nim_file          as nimF
    # from . import nim_rohtau_utils   as nimUtl
    # from . import nim_win as Win
else:
    # import nim                as Nim
    # import nim_api            as nimAPI
    # import nim_rohtau_utils   as nimUtl
    import nim_print          as nimP
    # import nim_win as Win

#  Variables :
from .import version 
from .import winTitle 
from .import padding 
from .import imgpadding 


#
# Globals
#
mwtt = 10 # Minimum working time for task (MWTT). In minutes

#
# Timecards Logging
#
def getTCLogsLoc():
    '''
    Get locations dir for time cards logs.
    Usually:
        /$TEMPDIR/timecards
    If location doesn't exists the create it.

    Parameters
    ----------
    

    Returns
    ---------
    str :
        Path to timecards location. If any error happens then False.    

    '''
    tmpdir = tempfile.gettempdir()
    if platform.system() != 'Windows':
        # In Unix the tmp folder doesnt have a user subfolder.
        tmpdir += "/%s"%getpass.getuser()
    logsdir = os.path.join(tmpdir, 'timecards')
    if not os.path.exists(logsdir):
        try:
            os.mkdir(logsdir)
        except FileExistsError as e:
            pass
        except Exception as e:
            nimP.error("Can't create temp folder for timecards, Check permission on temp folder: %s"%tmpdir, showwindow=True)
            return False

    return logsdir



def createTCLog(parent='', parentid=0, task='', taskid=0, typeid=0, userid=0, tcid=0):
    '''
    Check if there is already a timecard for the task.
    If not, create the log file.
    If it already exists then check close time for the card, if it is less then MWTT then reuse task and update close time.
    If the card is old enough then create a new one.

    Time Card Log Name Convention
    -----------------------------
    A time card log filename looks like:
        PARENT__TASK__TCID.json
    For instance, for a shot named SHL_030, task comp and a timecard id 1234:
        SHL_030__comp__1234.json
    So just extracting the pasrts of the file name we can know the parent, task and the id of the timecard, this is very handy to
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
    tcid : int
        Current Time Card in use id. 0 if there is no Time Card in use for current scene.
    

    Returns
    ---------
    str
        Path to timecard log file.

    '''
    logsdir = getTCLogsLoc()
    if not logsdir:
        return False
    
    logfiles = glob.glob(logsdir + '/*.json')
    tasklogs = []
    tcupdated = False
    tccreated = False
    for log in logfiles:
        filename = os.path.basename(log)
        filename = os.path.splitext(filename)[0]
        parts    = filename.split('__')
        if parts[0] == parent and parts[1] == task:
            if int(parts[2]) == tcid:
                # Found time card for current scene, just update end time
                # Call update TC
                if not updateTCLog(log):
                    return False
                tcupdated = True
                break
            else:
                # found potential usable timecard log.
                # Call to check time card, it suitable then update, if not then
                # create
                pass
    if not tcupdated or tccreated:
        # Need to create new time card
        tccreated = True
        pass


    return True


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
    bool
        True if everything went ok.    

    '''
    if not os.path.exists(logpath):
        nimP.error("Can't update Time Card log file, doesn't exists: %s"%logpath, showwindow=True)
        return False
    with (logpath"r") as logfile:
        tc = json.load(logfile)
    now = datetime.now()
    isonow = now.isoformat()
    timestamp = isonow.split('.')[0].split('T')[1] # Only get time without microseconds
    tc['end'] = timestamp

    # Write log back.
    with open(logpath, "w") as logfile:
        json.dump(tc, logfile, indent=2)

    return True

# TODO: implement checkTCLog
# Will check if we can use the timecard log


# TODO: implement createTCLog, Check name we are already using this funcion
# name.
# Create json file with correct name, at the moment use a random  id for TC,
# later we will implement publishing and do name correctly.
# Set time card id and log path in NIM data for the scene

    


    


    





#
# Timecards Logging
#





#
# Timecards Conform
#
