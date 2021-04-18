#!/usr/bin/env python
import os
import tempfile

__all__=['nim', 'nim_api', 'nim_file', 'nim_fileUI', 'nim_prefs', 'nim_print', 'nim_win', 'nim_rohtau', 'nim_rohtau_utils']


version     = 'v4.0.61 / rohtau v0.3' # Nim API version and rohtau version
winTitle    = 'NIM_'+version # Global title for all NIM windows
padding     = 3 # Global padding used for file versions.
imgpadding  = 4 # Global padding used for images files.
nimAPIConnectInfoFile = os.path.join(tempfile.gettempdir(), "nimAPIConnectInfo") # Temp file used to store API connection info for non login sessions. For instance, Deadline


#  END
