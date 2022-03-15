#!/usr/bin/env python
#******************************************************************************
#
# Filename: nim_print.py
# Version:  v4.0.61.210104
#
# Copyright (c) 2014-2021 NIM Labs LLC
# All rights reserved.
#
# Use of this software is subject to the terms of the NIM Labs license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# *****************************************************************************

#rohtau v0.2, python3 port



# Try to import nuke, if nuke is available, assume we are in Nuke and use
# nuke.tprint
isNuke = False
try:
    import nuke
    isNuke = True
except ImportError:
    pass

# Try to import hou, if Houdini is available
isHoudini = False
try:
    import hou
    isHoudini = True
except ImportError:
    pass


def debug( msg='' ) :
    'Custom info printer'
    debug = False
    #  Print :
    if debug =='True' and msg :
        tokens=msg.rstrip().split( '\n' )
        for toke in tokens :
            if isNuke:
                nuke.tprint('NIM.D-bug ~> %s' % toke)
            else:
                print('NIM.D-bug ~> %s' % toke)
        if msg[-1:]=='\n' :
            if isNuke:
                nuke.tprint('NIM.D-bug ~>')
            else:
                print('NIM.D-bug ~>')
    return


def info( msg='', showwindow=False  ) :
    'Custom info printer'
    if isinstance(msg, list):
        msg = ''.join(msg)
    tokens=msg.rstrip().split( '\n' )
    for toke in tokens :
        if isNuke:
            nuke.tprint('NIM ~> %s' % toke)
        else:
            print('NIM ~> %s' % toke)
    if showwindow:
        if isNuke and nuke.GUI:
            nuke.message(msg)
        elif isHoudini and hou.isUIAvailable():
            hou.ui.displayMessage(msg, title='NIM Error')
    if msg[-1:]=='\n' :
        if isNuke:
            nuke.tprint('NIM ~>')
        else:
            print('NIM ~>')
    return


def log( msg='' ) :
    'Custom info logger'
    if isinstance(msg, list):
        msg = ''.join(msg)
    tokens=msg.rstrip().split( '\n' )
    for toke in tokens :
        if isNuke:
            nuke.tprint('NIM.Log ~> %s' % toke)
        else:
            print('NIM.Log ~> %s' % toke)
    if msg[-1:]=='\n' :
        if isNuke:
            nuke.tprint('NIM.Log ~>')
        else:
            print('NIM.Log ~>')
    return


def warning( msg='', showwindow=False ) :
    'Custom warning printer'
    if isinstance(msg, list):
        msg = ''.join(msg)
    tokens=msg.rstrip().split( '\n' )
    for toke in tokens :
        if isNuke:
            nuke.tprint('NIM.Warning ~> %s' % toke)
            nuke.warning('NIM.Warning ~> %s' % toke)
        else:
            print('NIM.Warning ~> %s' % toke)
    if showwindow:
        if isNuke and nuke.GUI:
            nuke.alert(msg)
        elif isHoudini and hou.isUIAvailable():
            hou.ui.displayMessage(msg, title='NIM Error', severity=hou.severityType.Warning)
    if msg[-1:]=='\n' :
        if isNuke:
            nuke.tprint('NIM.Warning ~>')
            nuke.warning('NIM.Warning ~>')
        else:
            print('NIM.Warning ~>')
    return


def error( msg='', showwindow=False ) :
    'Custom error printer'
    if msg :
        if isinstance(msg, list):
            msg = ''.join(msg)
        tokens=msg.rstrip().split( '\n' )
        for toke in tokens :
            if isNuke:
                nuke.tprint('NIM.Error ~> %s' % toke)
                nuke.error('NIM.Error ~> %s' % toke )
            else:
                print('NIM.Error ~> %s' % toke)
        if msg[-1:]=='\n' :
            if isNuke:
                nuke.tprint('NIM.Error ~>')
                nuke.error('NIM.Error ~>')
            else:
                print('NIM.Error ~>')
        if showwindow:
            if isNuke and nuke.GUI:
                nuke.alert(msg)
            elif isHoudini and hou.isUIAvailable():
                hou.ui.displayMessage(msg, title='NIM Error', severity=hou.severityType.Error)
    else : 
        if isNuke:
            nuke.tprint('NIM.Error ~> An error was logged but no message was received.')
        else:
            print('NIM.Error ~> An error was logged but no message was received.')
    return


#  End

