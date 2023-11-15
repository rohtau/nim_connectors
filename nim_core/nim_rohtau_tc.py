'''
File:          nim_rohtau_tc.py
Project:       nim
File Created:  Tuesday, 26 April 2022 11:03:02
Author:        Pablo Gimenez (pablo@rohtau.com)
-----
Last Modified: Friday, 20 May 2022 01:29:38 CUT
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

import os,sys

pythonVersion = sys.version_info.major

if pythonVersion == 3 :
    # Import nim_core for Python3
    from .py3.nim_rohtau_tc import *

else :
    # Import nim_core for Python2
    from py2.nim_rohtau_tc import *
