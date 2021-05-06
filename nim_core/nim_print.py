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


def info( msg='' ) :
    'Custom info printer'
    tokens=msg.rstrip().split( '\n' )
    for toke in tokens :
        if isNuke:
            nuke.tprint('NIM ~> %s' % toke)
        else:
            print('NIM ~> %s' % toke)
    if msg[-1:]=='\n' :
        if isNuke:
            nuke.tprint('NIM ~>')
        else:
            print('NIM ~>')
    return


def log( msg='' ) :
    'Custom info logger'
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


def warning( msg='' ) :
    'Custom warning printer'
    tokens=msg.rstrip().split( '\n' )
    for toke in tokens :
        if isNuke:
            nuke.tprint('NIM.Warning ~> %s' % toke)
        else:
            print('NIM.Warning ~> %s' % toke)
    if msg[-1:]=='\n' :
        if isNuke:
            nuke.tprint('NIM.Warning ~>')
        else:
            print('NIM.Warning ~>')
    return


def error( msg='' ) :
    'Custom error printer'
    if msg :
        tokens=msg.rstrip().split( '\n' )
        for toke in tokens :
            if isNuke:
                nuke.tprint('NIM.Error ~> %s' % toke)
            else:
                print('NIM.Error ~> %s' % toke)
        if msg[-1:]=='\n' :
            if isNuke:
                nuke.tprint('NIM.Error ~>')
            else:
                print('NIM.Error ~>')
    else : 
        if isNuke:
            nuke.tprint('NIM.Error ~> An error was logged but no message was received.')
        else:
            print('NIM.Error ~> An error was logged but no message was received.')
    return


#  End

