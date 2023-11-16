#!/usr/bin/env python
import os
import tempfile

__all__=['nim', 'nim_api', 'nim_file', 'nim_fileUI', 'nim_prefs', 'nim_print', 'nim_win', 'nim_rohtau', 'nim_rohtau_utils']


version               = 'v6.1.4 / rohtau v0.6' # Nim API version and rohtau version
winTitle              = 'NIM_'+version # Global title for all NIM windows
padding               = 3 # Global padding used for file versions.
imgpadding            = 4 # Global padding used for images files.
nimAPIConnectInfoFile = os.path.join(tempfile.gettempdir(), "nimAPIConnectInfo") # Temp file used to store API connection info for non login sessions. For instance, Deadline
defaultSceneName      = 'main'
default_frame_range   = 100 # Default frame range. Use this value if frame range is no defined in NIM
mwtt                  = 1 # Minimum working time for task (MWTT). In minutes. Used to validate time cards


#  END
